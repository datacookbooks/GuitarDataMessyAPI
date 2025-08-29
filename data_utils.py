"""
Shared utility functions for data generation
"""
import numpy as np

def make_messy_id(original_id, is_distributor=False):
    """Make an id messy by randomly applying various transformations"""
    # 20% chance to keep original as int
    if np.random.random() < 0.2:
        return original_id

    # 30% chance to convert to string
    elif np.random.random() < 0.5:
        result = str(original_id)
        # 15% chance to add trailing space if it's a string
        if np.random.random() < 0.15:
            result += " "
        return result

    # 50% chance to add extra digits
    else:
        # For distributors (1-5), add extra digits like 111, 222, etc.
        # For models (1-9), add extra digits like 111, 222, etc.
        if is_distributor:
            # Convert 1->111, 2->222, 3->333, 4->444, 5->555
            messy_value = str(original_id) + str(original_id) + str(original_id)
        else:
            # For models, do the same pattern
            messy_value = str(original_id) + str(original_id) + str(original_id)

        # 60% chance to keep as string, 40% chance to convert to int
        if np.random.random() < 0.6:
            # 15% chance to add trailing space if keeping as string
            if np.random.random() < 0.15:
                messy_value += " "
            return messy_value
        else:
            return int(messy_value)


def make_messy_vendor_id(original_id):
    """Make vendor id messy by randomly applying various transformations"""
    # 30% chance to keep original as int
    if np.random.random() < 0.3:
        return original_id

    # 40% chance to convert to string
    elif np.random.random() < 0.7:
        result = str(original_id)
        # 20% chance to add trailing space if it's a string
        if np.random.random() < 0.2:
            result += " "
        return result

    # 30% chance to add extra digits (less frequent than in orders)
    else:
        # Convert 1->111, 2->222, 3->333
        messy_value = str(original_id) + str(original_id) + str(original_id)

        # 70% chance to keep as string, 30% chance to convert to int
        if np.random.random() < 0.7:
            # 20% chance to add trailing space if keeping as string
            if np.random.random() < 0.2:
                messy_value += " "
            return messy_value
        else:
            return int(messy_value)