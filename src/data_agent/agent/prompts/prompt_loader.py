from pathlib import Path


def load_prompt(file_name: str) -> str:
    """
    加载提示词
    Args:
        file_name (str): 提示词文件名称，不包含后缀

    Returns:
        str: 提示词文件内容
    """
    return (Path(__file__).parent / f"{file_name}.prompt").read_text(encoding="utf-8")
