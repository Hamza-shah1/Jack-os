import datetime


class Node:
    def __init__(self, name, is_file=False, owner="admin", permissions="rw-r--r--"):
        self.name = name
        self.is_file = is_file
        self.content = ""
        self.children = {}
        self.owner = owner
        self.permissions = permissions
        self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        self.size = 0

    def __repr__(self):
        kind = "FILE" if self.is_file else "DIR"
        return f"<{kind}: {self.name} | owner={self.owner} perms={self.permissions}>"


class FileSystem:
    def __init__(self):
        self.root = Node("root", is_file=False, owner="admin", permissions="rwxr-xr-x")
        self.current_path = []

    def _navigate(self, path):
        """Navigate to a node given a path list. Raises KeyError if not found."""
        current = self.root
        for part in path:
            if part not in current.children:
                raise KeyError(f"Path not found: {'/'.join(path)}")
            current = current.children[part]
        return current

    def create_dir(self, path, name, owner="admin"):
        """Create a directory at path/name."""
        parent = self._navigate(path)
        if name in parent.children:
            return False, f"'{name}' already exists"
        parent.children[name] = Node(name, is_file=False, owner=owner)
        return True, f"Directory '{name}' created"

    def create(self, path, name, is_file=True, owner="admin"):
        """Create a file or directory."""
        try:
            parent = self._navigate(path)
        except KeyError as e:
            return False, str(e)
        if name in parent.children:
            return False, f"'{name}' already exists"
        parent.children[name] = Node(name, is_file=is_file, owner=owner)
        return True, f"{'File' if is_file else 'Dir'} '{name}' created"

    def write(self, path, content, append=False):
        """Write content to a file."""
        try:
            node = self._navigate(path)
        except KeyError as e:
            return False, str(e)
        if not node.is_file:
            return False, f"'{path[-1]}' is a directory"
        if "w" not in node.permissions:
            return False, "Permission denied: no write permission"
        if append:
            node.content += content
        else:
            node.content = content
        node.size = len(node.content)
        node.modified = datetime.datetime.now()
        return True, "Written"

    def read(self, path):
        """Read content from a file."""
        try:
            node = self._navigate(path)
        except KeyError as e:
            return False, str(e)
        if not node.is_file:
            return False, "Cannot read a directory"
        if "r" not in node.permissions:
            return False, "Permission denied: no read permission"
        return True, node.content

    def delete(self, path):
        """Delete a file or empty directory."""
        if not path:
            return False, "Cannot delete root"
        try:
            parent = self._navigate(path[:-1])
            name = path[-1]
            node = parent.children.get(name)
            if node is None:
                return False, f"'{name}' not found"
            if not node.is_file and node.children:
                return False, f"Directory '{name}' is not empty"
            del parent.children[name]
            return True, f"'{name}' deleted"
        except KeyError as e:
            return False, str(e)

    def list_dir(self, path=None):
        """List contents of a directory."""
        if path is None:
            path = []
        try:
            node = self._navigate(path)
        except KeyError as e:
            return False, str(e)
        if node.is_file:
            return False, "Not a directory"
        entries = []
        for name, child in node.children.items():
            kind = "FILE" if child.is_file else "DIR"
            entries.append({
                "name": name,
                "type": kind,
                "size": child.size if child.is_file else "-",
                "owner": child.owner,
                "permissions": child.permissions,
                "modified": child.modified.strftime("%Y-%m-%d %H:%M"),
            })
        return True, entries

    def chmod(self, path, permissions):
        """Change permissions of a node."""
        try:
            node = self._navigate(path)
        except KeyError as e:
            return False, str(e)
        node.permissions = permissions
        return True, f"Permissions set to '{permissions}'"

    def move(self, src_path, dest_path, new_name=None):
        """Move/rename a file or directory."""
        try:
            src_parent = self._navigate(src_path[:-1])
            src_name = src_path[-1]
            node = src_parent.children.pop(src_name, None)
            if node is None:
                return False, f"Source '{src_name}' not found"
            dest_parent = self._navigate(dest_path)
            final_name = new_name or src_name
            node.name = final_name
            dest_parent.children[final_name] = node
            return True, f"Moved to '{final_name}'"
        except KeyError as e:
            return False, str(e)

    def tree(self, path=None, prefix=""):
        """Return a tree-formatted string of the filesystem."""
        if path is None:
            path = []
        try:
            node = self._navigate(path)
        except KeyError:
            return []
        lines = [f"{prefix}{'[D] ' if not node.is_file else '[F] '}{node.name}"]
        if not node.is_file:
            children = list(node.children.items())
            for i, (name, child) in enumerate(children):
                connector = "└── " if i == len(children) - 1 else "├── "
                extension = "    " if i == len(children) - 1 else "│   "
                sub = self.tree(path + [name], prefix + extension)
                lines.append(prefix + connector + sub[0].lstrip())
                lines.extend(sub[1:])
        return lines

    def search(self, name, path=None):
        """Search for files/dirs by name recursively."""
        if path is None:
            path = []
        results = []
        try:
            node = self._navigate(path)
        except KeyError:
            return results
        for child_name, child in node.children.items():
            if name.lower() in child_name.lower():
                results.append("/".join(path + [child_name]))
            if not child.is_file:
                results.extend(self.search(name, path + [child_name]))
        return results
