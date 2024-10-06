import threading
import PIL.Image
import imagehash
from bk_tree_parallel import BKTree
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fits aHash, pHash and hsvHash
def regulat_hash_hamming_distance(hash1, hash2):
    distance = hash1 - hash2
    return distance

# Fist only sHash
def sHash_hamming_distance(hash1, hash2):
    number_of_original_segments = len(hash1.segment_hashes)
    _, dist = hash1.hash_diff(hash2, hamming_cutoff=100)
    avg_block_hash_diff_1 = dist / number_of_original_segments
    return avg_block_hash_diff_1


class MinimalDistanceDetector:
    def __init__(self, aHash_threshold=5, pHash_threshold=17, hsvHash_threshold=3,
                 sHash_threshold=15):
        self.aHash_threshold = aHash_threshold
        self.pHash_threshold = pHash_threshold
        self.hsvHash_threshold = hsvHash_threshold
        self.sHash_threshold = sHash_threshold

        self.aHashTree = BKTree(regulat_hash_hamming_distance, self.aHash_threshold)
        self.pHashTree = BKTree(regulat_hash_hamming_distance, self.pHash_threshold)
        self.hsvHashTree = BKTree(regulat_hash_hamming_distance, self.hsvHash_threshold)
        self.sHashTree = BKTree(sHash_hamming_distance, self.sHash_threshold)


    def add_image_to_dataset(self, image: PIL.Image.Image, path=None):
        '''
        Calculates all four image hash values and adds each hash value to its BKTree.\n
        Important!!! No duplication check it done here, so duplications may be added to the tree.
        Users should call the check_if_duplication function first if they do not want duplications
        in the dataset.
        :param image:
        :return:
        '''
        aHash = imagehash.average_hash(image)
        self.aHashTree.add(aHash, path)

        pHash = imagehash.phash(image)
        self.pHashTree.add(pHash, path)

        hsvHash = imagehash.colorhash(image)
        self.hsvHashTree.add(hsvHash, path)

        sHash = imagehash.crop_resistant_hash(image)
        self.sHashTree.add(sHash, path)

        image.close()


    def check_image_for_duplications(self, image: PIL.Image.Image):
        '''
        Checks if the provided image is a duplication of an existing image in dataset.
        The check is performed parallel on all trees, and stops if one of the trees returns
        a positive indication.
        :param image:
        :return: True if found duplication, False otherwise
        '''
        aHash = imagehash.average_hash(image)
        pHash = imagehash.phash(image)
        hsvHash = imagehash.colorhash(image)
        sHash = imagehash.crop_resistant_hash(image)

        def serach_in_aHash_Tree(event):
            aMatch = self.aHashTree.search_within_distance(aHash)
            return aMatch is not None

        def serach_in_pHash_Tree(event):
            pMatch = self.pHashTree.search_within_distance(pHash)
            return pMatch is not None

        def serach_in_hsvHash_Tree(event):
            hsvMatch = self.hsvHashTree.search_within_distance(hsvHash)
            return hsvMatch is not None

        def serach_in_sHash_Tree(event):
            sMatch = self.sHashTree.search_within_distance(sHash, subtree_threshold=10)
            return sMatch is not None

        # Run parallel on all trees
        stop_event = threading.Event()
        detection_functions = [serach_in_aHash_Tree, serach_in_pHash_Tree, serach_in_hsvHash_Tree,
                     serach_in_sHash_Tree]

        found_duplication = False # The returned result
        with ThreadPoolExecutor(max_workers=len(detection_functions)) as executor:
            functions_future = {executor.submit(func, stop_event): func for func in detection_functions}

            for future in as_completed(functions_future):
                func = functions_future[future]
                try:
                    result = future.result()
                    if result == True:  # If any tree returns True, stop other trees
                        stop_event.set()
                        print(f"{func.__name__} found a match and set the stop event.")
                        found_duplication = True
                        break
                except Exception as exc:
                    print(f"{func.__name__} generated an exception: {exc}")

                # If one of the function returns a positive indication then stop all futures
                if stop_event.is_set():
                    for f in functions_future:
                        f.cancel()
                    break

        return found_duplication