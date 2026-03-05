import argparse
import os
import random

def parse_args():
    p = argparse.ArgumentParser(
        description="Split dataset IDs into train/valid/test sets."
    )
    p.add_argument(
        "--root",
        type=str,
        required=True,
        help="Dataset root (where file.list is located).",
    )
    p.add_argument(
        "--file-list",
        type=str,
        default=None,
        help="Path to file.list (default: <root>/file.list).",
    )
    p.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Fraction of data for train (default: 0.8).",
    )
    p.add_argument(
        "--valid-ratio",
        type=float,
        default=0.1,
        help="Fraction of data for valid (default: 0.1).",
    )
    p.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="Fraction of data for test (default: 0.1).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for shuffling (default: 0).",
    )
    return p.parse_args()

def main():
    args = parse_args()
    root = os.path.abspath(args.root)
    file_list = args.file_list or os.path.join(root, "file.list")

    total_ratio = args.train_ratio + args.valid_ratio + args.test_ratio
    if not (0.999 <= total_ratio <= 1.001):
        raise ValueError(
            f"Ratios must sum to 1.0, got {total_ratio:.4f} "
            f"(train={args.train_ratio}, valid={args.valid_ratio}, test={args.test_ratio})"
        )

    if not os.path.exists(file_list):
        raise FileNotFoundError(f"file.list not found: {file_list}")

    with open(file_list, "r") as f:
        ids = [ln.strip() for ln in f if ln.strip()]

    n = len(ids)
    if n == 0:
        raise RuntimeError("file.list is empty, nothing to split.")

    random.seed(args.seed)
    random.shuffle(ids)

    n_train = int(round(n * args.train_ratio))
    n_valid = int(round(n * args.valid_ratio))
    # ensure all go somewhere
    if n_train + n_valid > n:
        n_valid = n - n_train
    n_test = n - n_train - n_valid

    train_ids = ids[:n_train]
    valid_ids = ids[n_train:n_train + n_valid]
    test_ids  = ids[n_train + n_valid:]

    def write_ids(name, subset_ids):
        path = os.path.join(root, f"{name}.id")
        with open(path, "w") as f:
            for fid in subset_ids:
                f.write(fid + "\n")
        return path

    train_path = write_ids("train", train_ids)
    valid_path = write_ids("valid", valid_ids)
    test_path  = write_ids("test",  test_ids)

    print(f"Total IDs: {n}")
    print(f"  Train: {len(train_ids)}  -> {train_path}")
    print(f"  Valid: {len(valid_ids)}  -> {valid_path}")
    print(f"  Test:  {len(test_ids)}   -> {test_path}")

if __name__ == "__main__":
    main()
