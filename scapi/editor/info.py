from ..others import common

class Info:
    def __init__(self):
        self.useragent:str = f"Scapi/{common.__version__} Scratch Editor"
        self.semver:str = "3.0.0"
        self.vm = "11.1.0" # 開発に使ってたプロジェクトがこれだったので