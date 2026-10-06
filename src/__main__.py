if __name__ == "__main__":
    try:
        from sys import stderr
        from tqdm import tqdm

        with tqdm(desc="Loading modules", total=1) as bar:
            from .CLI import CLI
            bar.update()
        print()

        CLI()
    except KeyboardInterrupt:
        print("Interrupted", file=stderr)
        exit(1)
    except Exception as e:
        print(f"Error: {e}", file=stderr)
        exit(1)
