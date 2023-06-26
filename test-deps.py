import os
import ast
import sys


def get_used_modules(filepath):
    used_modules = set()

    with open(filepath, "r") as file:
        tree = ast.parse(file.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    used_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    used_modules.add(node.module.split(".")[0])

    return used_modules


def parse_dependency(dependency_line):
    # Split the line by '=='
    parts = dependency_line.strip().split(" ")
    package_name = parts[0].strip().split("#")[0].lower()
    if package_name.startswith("git+"):
        package_name = package_name.split("/")[-1]
    return package_name


def find_unused_dependencies(requirements_file):
    # Get all dependencies from requirements.txt
    with open(requirements_file, "r") as file:
        dependencies = [parse_dependency(line) for line in file if line.strip()]

    # Get used modules from Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        python_files.extend(
            [os.path.join(root, file) for file in files if file.endswith(".py")]
        )

    used_modules = set()
    for file in python_files:
        used_modules.update(get_used_modules(file))

    # Find unused dependencies
    unused_dependencies = [
        dependency for dependency in dependencies if dependency not in used_modules
    ]

    return unused_dependencies


if __name__ == "__main__":
    for requirements_file in sys.argv[1:]:
        unused_deps = find_unused_dependencies(requirements_file)

        if unused_deps:
            print("Unused dependencies found in {}:".format(requirements_file))
            for dependency in unused_deps:
                print(dependency)
        else:
            print("No unused dependencies found in {}.".format(requirements_file))
