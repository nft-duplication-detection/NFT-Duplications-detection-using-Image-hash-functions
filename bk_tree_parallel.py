from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class BKNode:
    def __init__(self, value, name):
        self.value = value
        self.image_name = name
        self.children = {}
        self.subtree_size = 1  # We obtain the subtree size for parallel optimization reasons

    def add_child(self, dist, child_node):
        self.children[dist] = child_node
        self.update_subtree_size()

    # Update the subtree size after adding an element
    def update_subtree_size(self):
        self.subtree_size = 1 + sum(child.subtree_size for child in self.children.values())


class BKTree:
    def __init__(self, distance_func, distance_threshold):
        self.root = None
        self.distance_func = distance_func
        self.distance_threshold = distance_threshold
        self.num_of_searches = 0

    def add(self, element, name):
        if self.root is None:
            self.root = BKNode(element, name)
        else:
            self._add_recursive(self.root, element, name)

    def _add_recursive(self, node, element, name):
        dist = self.distance_func(node.value, element)

        if dist in node.children:
            self._add_recursive(node.children[dist], element, name)
            node.update_subtree_size()
        else:
            # Create a new child node and update subtree sizes
            node.add_child(dist, BKNode(element, name))

    def search_within_distance(self, new_element, subtree_threshold=50):
        self.num_of_searches = 0
        found_flag = threading.Event()  # Thread-safe flag to indicate a match was found
        result_lock = threading.Lock()
        found_element = [None]  # Using a list since lists are mutable

        def parallel_bk_search(node, new_element, found_flag, lock, subtree_threshold):
            self.num_of_searches += 1
            # If a match has already been found, stop immediately
            if node is None or found_flag.is_set():
                return None

            # Calculate distance from new element to the current node
            dist = self.distance_func(new_element, node.value)

            # If we found an element in distance, return the element and signal stop
            if dist <= self.distance_threshold:
                with lock:
                    if not found_flag.is_set():  # Check again to avoid race conditions
                        found_element[0] = node.value
                        found_flag.set()  # Stop other threads
                return node.value

            # No reason to use parallelism if the subtree size is small enough
            if node.subtree_size < subtree_threshold:
                for child_dist, child_node in node.children.items():
                    if dist - self.distance_threshold <= child_dist <= \
                            dist + self.distance_threshold and not found_flag.is_set():
                        result = parallel_bk_search(child_node, new_element, found_flag, lock, subtree_threshold)
                        if result:
                            return result
            else:
                # Otherwise, parallelize the traversal
                tasks = []
                with ThreadPoolExecutor(max_workers=4) as executor:
                    for child_dist, child_node in node.children.items():
                        if dist - self.distance_threshold <= child_dist \
                                <= dist + self.distance_threshold and not found_flag.is_set():
                            tasks.append(
                                executor.submit(parallel_bk_search, child_node, new_element, found_flag, lock,
                                                subtree_threshold))

                    # Wait for all tasks to complete
                    for task in as_completed(tasks):
                        result = task.result()
                        if result:
                            return result

            return None

        if self.root is not None:
            parallel_bk_search(self.root, new_element, found_flag, result_lock, subtree_threshold)

        return found_element[0]  # Return the found element or None (if not found)