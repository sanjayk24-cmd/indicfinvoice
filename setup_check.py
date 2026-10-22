import sys

def check_environment() -> None:
    """Verify PyTorch version, CUDA availability, GPU name, and VRAM."""
    try:
        import torch
    except ImportError:
        print("Error: PyTorch is not installed.")
        print("Please install PyTorch with CUDA 12.8 using:")
        print("pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128")
        sys.exit(1)

    print(f"PyTorch Version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")

    if not cuda_available:
        print("\nCUDA is NOT available!")
        print("Please install PyTorch with CUDA 12.8 using:")
        print("pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128")
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    print(f"GPU Name: {device_name}")

    total_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    free_mem_bytes, total_mem_bytes = torch.cuda.mem_get_info(0)
    free_mem_gb = free_mem_bytes / (1024 ** 3)

    print(f"GPU Total Memory: {total_mem_gb:.2f} GB")
    print(f"GPU Free Memory: {free_mem_gb:.2f} GB")
    print("\nEnvironment check passed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    check_environment()
