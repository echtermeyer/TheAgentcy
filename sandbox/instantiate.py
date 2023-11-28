import os
from src.utils import write_str_to_file
from sandbox.dockergenerator import execute_python

class Python_Sandbox:

    def __init__(self, subfolder_path: str = "backend") -> None:

        # Get the directory of the current file
        # Join the current file directory with the subfolder path
        # Check if the directory exists, if not, create it
        current_file_dir = os.path.dirname(__file__)
        self.directory_path = os.path.join(current_file_dir, subfolder_path)
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

        # Instantiate basic python docker environment
        self.init_basic_environment()


    def trigger_execution_pipeline(self, fulltext_code: str) -> None:
        file_path = write_str_to_file(fulltext_code, self.directory_path, ".py")
        running_container = execute_python(file_path)

        print(running_container)
        pass


    def init_basic_environment(self):
        running_container = execute_python("""import flask
app = flask.Flask(__name__)
@app.route('/')
def home():
    return "Hello, World!"
if __name__ == '__main__':
    app.run(port=8000)""")
        pass
