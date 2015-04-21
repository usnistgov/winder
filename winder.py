import wx
try:
    from wx.dataview import TreeListCtrl
    wx_phoenix = True
except ImportError:
    raise ImportError("You must use wxpython phoenix version, classic doesn't work properly")
import wx.grid    
import json
from wx.dataview import TreeListCtrl
import time
import os
import shutil
import sys
import logging
import platform
import subprocess

if hasattr(sys, 'frozen'):
    app_root_path = os.path.dirname(sys.executable) 
else:
    app_root_path = os.path.dirname(__file__)
    
logging.basicConfig(filename=os.path.join(app_root_path, 'log.log'), filemode = 'w', level=logging.DEBUG)
logger = logging.getLogger()

class ModifyApplicationsDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, title = 'Set Bookmarks',  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, *args, **kwargs)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        self.grid = wx.grid.Grid(self)
        
        # Then we call CreateGrid to set the dimensions of the grid
        self.grid.CreateGrid(10, 3)
        self.grid.SetColLabelValue(0, 'Name')
        self.grid.SetColLabelValue(1, 'Path')
        self.grid.SetColLabelValue(2, 'Arguments')
        
        
        self.OK = wx.Button(self, label = 'Write')
        vsizer.Add(self.grid, flag = wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        vsizer.Add(self.OK, flag = wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self.SetSizer(vsizer)
        apps_path = os.path.join(app_root_path, 'apps.json')
        if os.path.exists(apps_path):
            apps = json.load(open(apps_path, 'r'))
            for i, ap in enumerate(apps):
                self.grid.SetCellValue(i, 0, ap['name'])
                self.grid.SetCellValue(i, 1, ap['path'])
                self.grid.SetCellValue(i, 2, ap['arguments'])
        
        self.grid.AutoSizeColumns()
        self.Fit()
        self.OK.Bind(wx.EVT_BUTTON, self.OnWrite)
        
    def OnWrite(self, event):
        apps_path = os.path.join(app_root_path, 'apps.json')
        with open(apps_path,'w') as fp:
            apps = []
            for i in range(10):
                n, p, a = [self.grid.GetCellValue(i, j) for j in range(3)]
                if n and p:
                    apps.append(dict(name = n, path = p, arguments = a))
            json.dump(apps, fp, indent = 4)
        self.Close()

class ModifyBookmarksDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, title = 'Set Bookmarks', *args, **kwargs)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        self.grid = wx.grid.Grid(self)
        
        # Then we call CreateGrid to set the dimensions of the grid
        self.grid.CreateGrid(10, 2)
        self.grid.SetColLabelValue(0, 'Name')
        self.grid.SetColLabelValue(1, 'Path')
        self.OK = wx.Button(self, label = 'Write')
        vsizer.Add(self.grid, flag = wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        vsizer.Add(self.OK, flag = wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        self.SetSizer(vsizer)
        self.Fit()
        book_path = os.path.join(app_root_path, 'bookmarks.json')
        if os.path.exists(book_path):
            bookmarks = json.load(open(book_path,'r'))
            for i,mark in enumerate(bookmarks):
                self.grid.SetCellValue(i, 0, mark['name'])
                self.grid.SetCellValue(i, 1, mark['path'])
        
        self.OK.Bind(wx.EVT_BUTTON, self.OnWrite)
        
    def OnWrite(self, event):
        book_path = os.path.join(app_root_path, 'bookmarks.json')
        with open(book_path,'w') as fp:
            bookmarks = []
            for i in range(10):
                bookmarks.append(dict(name = self.grid.GetCellValue(i, 0), path = self.grid.GetCellValue(i, 1)))
            json.dump(bookmarks, fp, indent = 4)
        self.Close()
        
def ErrorMessage(msg):
    dlg = wx.MessageDialog(None, msg)
    dlg.ShowModal()
    dlg.Destroy()
    
def dirs_and_files(root):
    try:
        things = os.listdir(root)
    except WindowsError as WE:
        logging.info("Unable to enter " + root)
        return [], []
    dirs = [thing for thing in things if os.path.isdir(os.path.join(root, thing)) ]
    files = [thing for thing in things if thing not in dirs]
    return dirs, files

col_tree = 0
col_size = 1
col_day = 2
col_time = 3
        
class ItemComparator(wx.dataview.TreeListItemComparator):
    """ This class is used to determine how to sort a given column """
    def Compare(self, treelist, column, first, second):
        if column == col_tree:
            path_first = treelist.Parent.ItemToAbsPath(first)
            path_second = treelist.Parent.ItemToAbsPath(second)
            first_text = treelist.GetItemText(first, column)
            second_text = treelist.GetItemText(second, column)
            isdir_first = os.path.isdir(path_first)
            isdir_second = os.path.isdir(path_second)
            
            if isdir_first and not isdir_second: # First is a directory, second is not a directory
                return -1
            elif isdir_second and not isdir_first: # Second is a directory, first is not a directory
                return 1
            
            try: # Either both files or both directories
                f,s = sorted((first_text, second_text))
                if first_text == f:
                    return -1
                else:
                    return 1
            except ValueError as VE:
                print(treelist.GetItemText(first, 0), treelist.GetItemText(first, column),treelist.GetItemText(second, column))
                print VE
                return 0

        elif column == col_size:
            first_text = treelist.GetItemText(first,column).replace(',','')
            second_text = treelist.GetItemText(second,column).replace(',','')
            if first_text and not second_text: # First is a file, second is a directory
                return 1
            elif second_text and not first_text: #second is a file, first is a directory
                return -1
            if first_text and second_text:
                try:
                    return int( float(first_text) - float(second_text) )
                except ValueError:
                    print(treelist.GetItemText(first, 0), treelist.GetItemText(first, column),treelist.GetItemText(second, column))
                    return 0
            else:
                return 0
        elif column in [col_day, col_time]:
            path_first = treelist.Parent.ItemToAbsPath(first)
            mtime_first = os.path.getmtime(path_first)
            path_second = treelist.Parent.ItemToAbsPath(second)
            mtime_second = os.path.getmtime(path_second)
            isdir_first = os.path.isdir(path_first)
            isdir_second = os.path.isdir(path_second)
            if isdir_first == isdir_second: # Both files or both directories
                return mtime_first - mtime_second
            else:
                return int(isdir_second) - int(isdir_first)
        else:
            return 0
comparator = ItemComparator()

class NodeData:
    expanded = False
    
class MainFrame(wx.Frame):
    """
    This is the main frame of the program, into which the tree is put
    
    Functions that start with "On" are event handlers, which you can see because event is the second argument to the function
    """
    def __init__(self, parent, root_path = os.path.expanduser("~"), *args, **kwargs):
        size = (800, 800) #Default size
        
        # If preferences.json exists, load it and use it to specify the window size
        pref_path = os.path.join(app_root_path, 'preferences.json')
        if os.path.exists(pref_path):
            with open(pref_path,'r') as fp:
                options = json.load(fp)
                if 'size' in options:
                    size = options['size']
        wx.Frame.__init__(self, parent, title='Winder', *args, size = size, **kwargs)        
        
        self.make_menu_bar()
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        self.tree = TreeListCtrl(self, -1, style = wx.dataview.TL_MULTIPLE | wx.dataview.TL_CHECKBOX )

        self.isz = (16,16)
        il = wx.ImageList(*self.isz)
        self.fldridx     = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, self.isz))
        self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, self.isz))
        self.fileidx     = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, self.isz))

        self.tree.SetImageList(il)
        self.il = il
            
        self.root_path = root_path
        self.build_tree()
        
        # Set the acceleratators to manually intercept some keystrokes
        self.set_accelerators()
        vsizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(vsizer)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def build_tree(self):
        
        self.tree.ClearColumns()
        self.tree.DeleteAllItems()
        
        # create some columns
        self.tree.AppendColumn("Main column", align = wx.ALIGN_RIGHT, flags = wx.COL_SORTABLE|wx.COL_RESIZABLE)
        self.tree.AppendColumn("Size (B)", width = wx.COL_WIDTH_AUTOSIZE, align = wx.ALIGN_RIGHT, flags = wx.COL_SORTABLE|wx.COL_RESIZABLE)
        self.tree.AppendColumn("Day", width = wx.COL_WIDTH_AUTOSIZE, align = wx.ALIGN_RIGHT, flags = wx.COL_SORTABLE|wx.COL_RESIZABLE)
        self.tree.AppendColumn("Time", width = wx.COL_WIDTH_AUTOSIZE, align = wx.ALIGN_RIGHT, flags = wx.COL_SORTABLE|wx.COL_RESIZABLE)
        self.tree.AppendColumn("", width = 20, align = wx.ALIGN_RIGHT, flags = wx.COL_SORTABLE|wx.COL_RESIZABLE)
        
        self.root = self.tree.AppendItem(self.tree.GetRootItem(), self.root_path, self.fldridx, self.fldropenidx)
        
        self.tree.GetView().Bind(wx.EVT_KEY_DOWN, self.OnTreeKeyPress)
        self.tree.GetView().Bind(wx.EVT_CHAR, self.OnTreeChar)
        self.Bind(wx.dataview.EVT_TREELIST_ITEM_ACTIVATED, self.OnTreeDoubleClick, self.tree)
        self.tree.GetDataView().Bind(wx.dataview.EVT_DATAVIEW_COLUMN_HEADER_CLICK, self.OnHeaderClick)
        self.Bind(wx.dataview.EVT_TREELIST_ITEM_EXPANDING, self.OnExpandTreeListLeaf, self.tree)
                
        self.populate_tree(self.root, self.root_path)
        
        self.tree.SetItemComparator(comparator)
        self.tree.Expand(self.root)
        
        for col in [col_size, col_day, col_time]:
            self.tree.SetColumnWidth(col, self.tree.GetColumnWidth(col) + 5)
        
    def populate_tree(self, parent, root_path, recurse = True):
        """
        Lazily populate the TreeListCtrl for given item
        
        parent(TreeListItem) : The parent node in the tree
        root_path(str) : The absolute path in the OS to the 
        recurse(bool) : Keep going deeper into the tree
        """
        day_fmt = " %m-%d-%y "
        time_fmt = " %I:%M:%S %p "
        
        # Don't add again children if parent item is already expanded
        # But DO recurse into directories contained by the parent directory
        data = self.tree.GetItemData(parent)
        if data is None or data.expanded == False:
        
            # We are going to populate!
            
            # Get the directories and files contained in this folder
            dirs, files = dirs_and_files(root_path)
            
            for dirname in dirs:
                child = self.tree.AppendItem(parent, dirname, self.fldridx, self.fldropenidx)
                self.tree.SetItemText(child, col_size, "")
                complete_path = os.path.join(root_path, dirname)
                mtime = time.localtime(os.path.getmtime(complete_path))
                self.tree.SetItemText(child, col_day, str(time.strftime(day_fmt, mtime)))
                self.tree.SetItemText(child, col_time, str(time.strftime(time_fmt, mtime)))
            
            for file in files:
                child = self.tree.AppendItem(parent, file, self.fileidx, self.fileidx)
                complete_path = os.path.join(root_path, file)
                filesize_kb = os.path.getsize(complete_path)
                self.tree.SetItemText(child, col_size, '{:,}'.format(filesize_kb))
                mtime = time.localtime(os.path.getmtime(complete_path))
                self.tree.SetItemText(child, col_day, str(time.strftime(day_fmt, mtime)))
                self.tree.SetItemText(child, col_time, str(time.strftime(time_fmt, mtime)))
            
        # The top level has been populated if needed, now recurse into 
        # directories and populate them one more level
        if recurse:
            # Visit all the children of the parent
            item = self.tree.GetFirstChild(parent)
            while item.IsOk():
                if self.ItemIsDirectory(item):
                    # Go down one more level
                    self.populate_tree(item, self.ItemToAbsPath(item), recurse = False)
                # Go to next sibling in this directory
                item = self.tree.GetNextSibling(item)
            
        # Set the flag telling you that the parent has been populated
        data = NodeData()
        data.expanded = True
        self.tree.SetItemData(parent, data)
    
    def OnHeaderClick(self, event):
        sorted, col, ascendingOrder = self.tree.GetSortColumn()
        if event.GetColumn() == col and sorted and ascendingOrder == True:
            event.Veto()
        else:
            event.Skip()
        
    def ItemToAbsPath(self, item):
        """ Build the absolute path to the item by walking back up the tree"""
        parts = []
        while item.IsOk():
            # Get the next part
            part = self.tree.GetItemText(item, col_tree)
            if part:
                # Prepend this part
                parts.insert(0, part)
            # Walk up the tree one level
            item = self.tree.GetItemParent(item)
            
        path = os.path.sep.join(parts)
        return path
        
    def ItemIsDirectory(self, item):
        return os.path.isdir(self.ItemToAbsPath(item))
        
    def OnExpandTreeListLeaf(self, event):
        items = self.tree.GetSelections()
        if items:
            fname = self.tree.GetItemText(items[0], col_tree)
            self.populate_tree(items[0], self.ItemToAbsPath(items[0]))
        
    def OnTreeDoubleClick(self, event):
        if 'win' in sys.platform:
            items = self.tree.GetSelections()
            if len(items) != 1: 
                ErrorMessage("Must select one thing in tree")
                return
            path = self.ItemToAbsPath(items[0])
            if path.upper().endswith('.EXE'):
                self.OnRunExecutable(event)
        else:
            logging.log('Cannot double-click launch on non-windows platform')
        
    def OnTreeChar(self, event = None):
        keycode = event.GetKeyCode()
        
        # Toggle the value in the first column
        def toggle(items):
            for s in items:
                if self.tree.GetCheckedState(s) == wx.CHK_CHECKED:
                    self.tree.CheckItem(s, wx.CHK_UNCHECKED)
                else:
                    self.tree.CheckItem(s, wx.CHK_CHECKED)
        if keycode == ord('*'):
            if len(self.tree.GetSelections()) != 1:
                wx.LogMessage("Can only select one item for glob select with *")
                
            item = self.tree.GetSelections()[0]
            # Get the file extension of the selected entity    
            root_ext = os.path.splitext(self.tree.GetItemText(item, col_tree))[1]
            
            if self.ItemIsDirectory(item):
                wx.LogMessage("Can only apply glob select to files")
                return
            
            # Rewind to the first sibling
            parent = self.tree.GetItemParent(item)
            item = self.tree.GetFirstChild(parent)
                
            while item.IsOk():
                fname = self.tree.GetItemText(item, col_tree)
                
                ext = os.path.splitext(fname)[1]
                if ext and ext.upper() == root_ext.upper() and not self.ItemIsDirectory(item):
                    toggle([item])
                item = self.tree.GetNextSibling(item)
        else:
            event.Skip()
                    
    def OnTreeKeyPress(self, event = None):
        # Toggle the value in the first column
        def toggle(items):
            for s in items:
                if self.tree.GetCheckedState(s) == wx.CHK_CHECKED:
                    self.tree.CheckItem(s, wx.CHK_UNCHECKED)
                else:
                    self.tree.CheckItem(s, wx.CHK_CHECKED)
            
        keycode = event.GetUnicodeKey()
        if keycode == wx.WXK_SPACE or keycode == ' ':
            if len(self.tree.GetSelections()) > 1:
                for s in self.tree.GetSelections():
                    if self.ItemIsDirectory(s):
                        wx.LogMessage("Cannot use directory as part of multi-select")
                        return
                toggle(self.tree.GetSelections())
                
            else:
                item = self.tree.GetSelections()[0] # Only one selection for sure
                if not self.ItemIsDirectory(item):
                    toggle(self.tree.GetSelections())
                else:
                    # If a directory, select all files (but not subdirectories) in the directory
                    item = self.tree.GetFirstChild(item)
                    
                    while item.IsOk():
                        if self.ItemIsDirectory(item): 
                            item = self.tree.GetNextSibling(item)
                            continue
                        else:
                            toggle([item])
                        item = self.tree.GetNextSibling(item)
        elif event.GetKeyCode() == wx.WXK_ESCAPE:
            self.UncheckAllItems()
            event.Skip()
        else:
            #print keycode, type(keycode), event.GetKeyCode(), wx.WXK_ESCAPE
            event.Skip()
        
    def set_accelerators(self):
        # See http://www.blog.pythonlibrary.org/2010/12/02/wxpython-keyboard-shortcuts-accelerators/
        accelEntries = []
        for key in ['F', 'D', 'A', 'X', 'R', 'O']:

            eventId = wx.NewId()
            accelEntries.append( (wx.ACCEL_NORMAL, ord(key), eventId) )

            self.Bind(wx.EVT_MENU, lambda evt, _id=eventId, _key = key: self.OnManualAccelerator(evt, _id, _key), id=eventId)
        
        accelTable  = wx.AcceleratorTable(accelEntries)
        self.SetAcceleratorTable(accelTable )
                
    def OnManualAccelerator(self, event, id, key):
        #for menu, label in self.menuBar.GetMenus():
        #    print menu, label, menu.GetWindow().GetScreenPosition(), menu.GetWindow().GetScreenPosition()
        #print self.menuBar.GetScreenPosition()
        
        treepos = self.tree.GetScreenPosition()
        #print treepos
        coords = self.ScreenToClient(treepos)
        if key == 'F':
            mnu = self.make_file_menu(self)
        elif key == 'D':
            mnu = self.make_directory_menu(self)
        elif key == 'A':
            mnu = self.make_applications_menu(self)
        elif key == 'O':
            mnu = self.make_options_menu(self)
        elif key == 'R':
            self.OnRunExecutable(self)
            return
        elif key == 'X':
            self.OnClose()
            return
        else:
            ErrorMessage("Not able to process keystroke " + key)
        self.PopupMenu(mnu, wx.Point(coords.x, coords.y))
        
    def OnWriteDirectory(self, event):
        
        item = self.tree.GetFirstChild(self.root)
            
        text = []
        while item.IsOk():
            if self.tree.IsVisible(item):
        
                name = self.tree.GetItemText(item, col_tree)
                size = self.tree.GetItemText(item, col_size)
                day = self.tree.GetItemText(item, col_day)
                time = self.tree.GetItemText(item, col_time)
                line = "{name:s}\t{size:s}\t{day:s}\t{time:s}".format(**locals())
                text.append(line)
                
            item = self.tree.GetNext(item)
        
        dlg = wx.FileDialog(
            self, message="Select output file", defaultDir=os.getcwd(), 
            defaultFile="", style=wx.SAVE
            )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w') as fp:
                fp.write('\n'.join(text))
        dlg.Destroy()
    
    def UncheckAllItems(self):        
        item = self.root
        items = []
        while item.IsOk():
            self.tree.CheckItem(item, wx.CHK_UNCHECKED)
            item = self.tree.GetNextItem(item)
        return items
        
    def GetMarkedItems(self):        
        item = self.tree.GetFirstChild(self.root)
        items = []
        while item.IsOk():
            if self.tree.GetCheckedState(item) == wx.CHK_CHECKED:
                items.append(item)
            item = self.tree.GetNextItem(item)
        return items

    def OnRemoveDirectory(self, event):
        items = self.tree.GetSelections()
        if len(items) != 1: 
            ErrorMessage("Must select one thing in tree")
            return
        path = self.ItemToAbsPath(items[0])
        if not self.ItemIsDirectory(items[0]): 
            ErrorMessage("Selected entity is not a directory")
            return
        try:
            os.rmdir(path)
        except OSError:
            ErrorMessage("Selected directory is not empty")
            
        self.build_tree()
        
    def OnRemoveFile(self, event):
        items = self.tree.GetSelections()
        if len(items) == 0: 
            ErrorMessage("Must select at least one file in tree")
            return
        if any([self.ItemIsDirectory(item) for item in items]):
            ErrorMessage("Cannot remove directories")
            return
        
        for item in items:
            path = self.ItemToAbsPath(item)
            try:
                os.remove(path)
            except OSError:
                ErrorMessage("Cannot remove file" + path)
            
        self.build_tree()
    
    def OnRenameFile(self, event):
        items = self.tree.GetSelections()
        if len(items) != 1: 
            ErrorMessage("Must select one thing in tree")
            return
        fname = self.tree.GetItemText(items[0],col_tree)
        path = self.ItemToAbsPath(items[0])
        if self.ItemIsDirectory(items[0]): 
            ErrorMessage("Selected entity is not a file")
            return
        dlg = wx.TextEntryDialog(
                self, 'New file name',
                'Was' + path, fname)
                
        if dlg.ShowModal() == wx.ID_OK:
            try:
                os.rename(path, os.path.join(os.path.dirname(path), dlg.GetValue()))
                self.build_tree()
            except OSError:
                ErrorMessage("Rename target already exists")
        dlg.Destroy()
        
    def OnRenameDirectory(self, event):
        items = self.tree.GetSelections()
        if len(items) != 1: 
            ErrorMessage("Must select one thing in tree")
            return
        fname = self.tree.GetItemText(items[0],col_tree)
        path = self.ItemToAbsPath(items[0])
        if not self.ItemIsDirectory(items[0]): 
            ErrorMessage("Selected entity is not a directory")
            return
        dlg = wx.TextEntryDialog(
                self, 'New directory name',
                'Was' + path, fname)
                
        if dlg.ShowModal() == wx.ID_OK:
            try:
                os.rename(path, os.path.join(os.path.dirname(path),dlg.GetValue()))
                self.build_tree()
            except OSError:
                ErrorMessage("Rename target already exists")
        dlg.Destroy()
        
    def OnNewDirectory(self, event):
        """ Event handler to make a new directory """
        items = self.tree.GetSelections()
        if len(items) != 1: 
            ErrorMessage("Must select one thing in tree")
        path = self.ItemToAbsPath(items[0])
        root = os.path.dirname(path)
        dlg = wx.TextEntryDialog(
                self, 'New directory to be added to ' + root,
                'New directory', '')
        if dlg.ShowModal() == wx.ID_OK:
            os.mkdir(os.path.join(root, dlg.GetValue()))
        dlg.Destroy()
        self.build_tree()
        
    def OnLoadBookmark(self, event, path):
        self.root_path = path
        self.build_tree()
            
    def OnChangePath(self, event):
        # In this case we include a "New directory" button. 
        dlg = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            self.root_path = dlg.GetPath()
            self.build_tree()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        
    def OnChangeDrive(self, event):
        if 'win' in sys.platform:
            try:
                import win32api
            except ImportError:
                ErrorMessage("Unable to import win32api")
                return
        else:
            print 'no such thing as drive on this platform'

        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        
        dlg = wx.SingleChoiceDialog(
                self, 'Select Working Drive:', 'Drive?',
                drives, 
                wx.CHOICEDLG_STYLE
                )

        if dlg.ShowModal() == wx.ID_OK:
            self.root_path = dlg.GetStringSelection()
            self.build_tree()

        dlg.Destroy()
        
    def OnChar(self, event):
        keycode = event.GetUnicodeKey()
        if keycode != wx.WXK_NONE:
            # It's a printable character
            wx.LogMessage("You pressed '%c'"%keycode)
        else:
            wx.LogMessage("You pressed a non ASCII key '%c'"%keycode)
            
    
    
    def OnFileCopy(self, event = None):
        source_items = self.GetMarkedItems()
        if len(source_items) == 0: 
            ErrorMessage("At least one file must be marked")
            return
        items = self.tree.GetSelections()
        if len(items) != 1:
            ErrorMessage("One target directory must be selected")
            return
        if not self.ItemIsDirectory(items[0]):
            ErrorMessage("Target must be a directory")
            return
        new_dir = self.ItemToAbsPath(items[0])
        # Prepare paths (to make sure we don't have collision)
        paths = []
        for item in source_items:
            old_path = self.ItemToAbsPath(item)
            old_fname = self.tree.GetItemText(item, col_tree)
            new_path = os.path.join(new_dir, old_fname)
            paths.append((old_path, new_path))
        old, new = zip(*paths)
        if len(paths) != len(set(new)):
            ErrorMessage("At least two destination files have the same name")
            return
        if any([os.path.exists(n) for n in new]):
            dlg = wx.MessageDialog(self, 'Some output files will be over-written, Yes to continue and over-write',
                               'Over-write?',
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION
                               )
            if dlg.ShowModal() == wx.ID_NO:                
                dlg.Destroy()
                return
        # And here goes the copy
        for (old, new) in paths:
            shutil.copy2(old, new)
            
        self.build_tree()
        
    def OnFileMove(self, event = None):
        source_items = self.GetMarkedItems()
        if len(source_items) == 0: 
            ErrorMessage("At least one file must be marked")
            return
        items = self.tree.GetSelections()
        if len(items) != 1:
            ErrorMessage("One target directory must be selected")
            return
        if not self.ItemIsDirectory(items[0]):
            ErrorMessage("Target must be a directory")
            return
        new_dir = self.ItemToAbsPath(items[0])
        # Prepare paths (to make sure we don't have collision)
        paths = []
        for item in source_items:
            old_path = self.ItemToAbsPath(item)
            old_fname = self.tree.GetItemText(item, col_tree)
            new_path = os.path.join(new_dir, old_fname)
            paths.append((old_path, new_path))
        old, new = zip(*paths)
        print old, new
        if len(paths) != len(set(new)):
            ErrorMessage("At least two destination files have the same name")
            return
        if any([os.path.exists(n) for n in new]):
            dlg = wx.MessageDialog(self, 'Some output files will be over-written, Yes to continue and over-write',
                               'Over-write?',
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION
                               )
            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
                return
        # And here goes the move
        for (old, new) in paths:
            shutil.move(old, new)
            
        self.build_tree()
    
    def OnClose(self, evnt = None):
        dlg = wx.MessageDialog(self, 'Quit?',
                               'Quit?',
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION
                               )
        if dlg.ShowModal() == wx.ID_YES:
            pref_path = os.path.join(app_root_path, 'preferences.json')
            if os.path.exists(pref_path):
                with open(pref_path, 'r') as fp:
                    options = json.load(fp)
                    options['size'] = list(self.GetSize())
                with open(pref_path, 'w') as fp:
                    json_string = json.dumps(options)
                    fp.write(json_string)
                    
            self.Destroy()
        dlg.Destroy()
    
    def OnModifyBookmarks(self, event = None):
        dlg = ModifyBookmarksDialog(None)
        dlg.ShowModal()
        dlg.Destroy()
        
    def OnModifyApplications(self, event = None):
        dlg = ModifyApplicationsDialog(None)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnApplicationLaunch(self, event, menu):
        items = self.tree.GetSelections()
        if len(items) != 1:
            ErrorMessage("One file must be selected")
            return
        file_path = os.path.normpath(self.ItemToAbsPath(items[0]))
        name = menu.GetLabel()
        
        # See http://stackoverflow.com/a/12144179/1360263
        # define a command that starts new terminal
        if platform.system() == "Windows":
            new_window_command = "cmd /S /C"
        else:  #XXX this can be made more portable
            new_window_command = "x-terminal-emulator -e".split()
            
        app_path = None
        for app in self.apps:
            if app['name'].replace('&','') == name: # Remove accelerator symbol
                app_path = app['path']
                break
        if app_path is None:
            ErrorMessage("Could not match app name: " + name)
            return
        command = ' '.join([app_path, file_path])
        call_string = new_window_command + '"' + command + '"'
        subprocess.Popen(call_string, cwd = os.path.dirname(file_path), shell = False)
        
    def OnRunExecutable(self, event):
        items = self.tree.GetSelections()
        if len(items) != 1:
            ErrorMessage("One file must be selected")
            return
        exe_path = self.ItemToAbsPath(items[0])
        
        # See http://stackoverflow.com/a/12144179/1360263
        # define a command that starts new terminal
        if platform.system() == "Windows":
            new_window_command = "cmd.exe /c "
        else:  #XXX this can be made more portable
            new_window_command = "x-terminal-emulator -e".split()
        
        dlg = wx.TextEntryDialog(
                self, 'Additional command line arguments',
                'Arguments', "")
                
        if dlg.ShowModal() == wx.ID_OK:
            arguments = dlg.GetValue().split(' ')
        else:
            arguments = []
        dlg.Destroy()
        if arguments:
            arguments = ' '.join(['"' + arg + '"' for arg in arguments if arg])
                
            call_string = new_window_command + '""' + exe_path + '"' + arguments + '"'
            from subprocess import CREATE_NEW_CONSOLE
            subprocess.Popen(call_string, cwd = os.path.dirname(exe_path), shell = False, creationflags=CREATE_NEW_CONSOLE)
        
    def make_options_menu(self, parent):
        """
        As the name implies, construct the options menu and return it
        """
        def set_bookmarks():
            book_path = os.path.join(app_root_path, 'bookmarks.json')
            if os.path.exists(book_path):
                bookmarks = json.load(open(book_path, 'r'))
                for i,mark in enumerate(bookmarks):
                    menu.BookMarks[i].SetText(str(i+1)+ ': ' + mark['name'])
                    parent.Bind(wx.EVT_MENU, lambda evt, path = mark['path']: parent.OnLoadBookmark(evt, path), menu.BookMarks[i])
                    
        menu = wx.Menu()
        menu.Refresh = wx.MenuItem(menu, -1, "&Refresh\tF5", "", wx.ITEM_NORMAL)
        menu.sep = wx.MenuItem(menu, -1, "", "", wx.ITEM_SEPARATOR)
        menu.book = wx.MenuItem(menu, -1, "**Bookmarks**", "", wx.ITEM_NORMAL)
        menu.BookMarks = []
        for i in range(10):
            menu.BookMarks.append(wx.MenuItem(menu, -1, " ", " ", wx.ITEM_NORMAL))
        menu.ModifyBookmarks = wx.MenuItem(menu, -1, "Modify...", "", wx.ITEM_NORMAL)
        
        for el in [menu.Refresh, menu.sep, menu.book] + menu.BookMarks + [menu.ModifyBookmarks]:
            if wx_phoenix:
                menu.Append(el)
            else:
                menu.AppendItem(el)
        parent.Bind(wx.EVT_MENU, lambda evt: self.build_tree(), menu.Refresh)
        parent.Bind(wx.EVT_MENU, parent.OnModifyBookmarks, menu.ModifyBookmarks)
        set_bookmarks()
        return menu
        
    def make_directory_menu(self, parent):
        """
        As the name implies, construct the directory menu and return it
        """
        menu = wx.Menu()
        menu.Drive = wx.MenuItem(menu, -1, "Change &Drive", "", wx.ITEM_NORMAL)
        menu.Path = wx.MenuItem(menu, -1, "Change &Path", "", wx.ITEM_NORMAL)
        menu.Sort = wx.MenuItem(menu, -1, "&Sort (WIP)", "", wx.ITEM_NORMAL)
        menu.New = wx.MenuItem(menu, -1, "&New", "", wx.ITEM_NORMAL)
        menu.Erase = wx.MenuItem(menu, -1, "&Erase", "", wx.ITEM_NORMAL)
        menu.Rename = wx.MenuItem(menu, -1, "&Rename", "", wx.ITEM_NORMAL)
        menu.Write = wx.MenuItem(menu, -1, "&Write", "", wx.ITEM_NORMAL)
        for el in [menu.Drive, menu.Path, menu.Sort, menu.New, menu.Erase, menu.Rename, menu.Write]:
            if wx_phoenix:
                menu.Append(el)
            else:
                menu.AppendItem(el)
        parent.Bind(wx.EVT_MENU, parent.OnNewDirectory, menu.New)
        parent.Bind(wx.EVT_MENU, parent.OnRemoveDirectory, menu.Erase)
        parent.Bind(wx.EVT_MENU, parent.OnRenameDirectory, menu.Rename)
        parent.Bind(wx.EVT_MENU, parent.OnChangePath, menu.Path)
        parent.Bind(wx.EVT_MENU, parent.OnChangeDrive, menu.Drive)
        parent.Bind(wx.EVT_MENU, parent.OnWriteDirectory, menu.Write)
        return menu
    
    def make_file_menu(self, parent):
        """
        As the name implies, construct the file menu and return it
        """
        menu = wx.Menu()
        menu.Find = wx.MenuItem(menu, -1, "&Find (WIP)", "", wx.ITEM_NORMAL)
        menu.Copy = wx.MenuItem(menu, -1, "&Copy", "", wx.ITEM_NORMAL)
        menu.Rename = wx.MenuItem(menu, -1, "&Rename", "", wx.ITEM_NORMAL)
        menu.Move = wx.MenuItem(menu, -1, "&Move", "", wx.ITEM_NORMAL)
        menu.Erase = wx.MenuItem(menu, -1, "&Erase", "", wx.ITEM_NORMAL)
        menu.Attrib = wx.MenuItem(menu, -1, "&Attrib (WIP)", "", wx.ITEM_NORMAL)
        for el in [menu.Find, menu.Copy, menu.Rename, menu.Move, menu.Erase, menu.Attrib]:
            if wx_phoenix:
                menu.Append(el)
            else:
                menu.AppendItem(el)
        parent.Bind(wx.EVT_MENU, parent.OnFileCopy, menu.Copy)
        parent.Bind(wx.EVT_MENU, parent.OnFileMove, menu.Move)
        parent.Bind(wx.EVT_MENU, parent.OnRemoveFile, menu.Erase)
        parent.Bind(wx.EVT_MENU, parent.OnRenameFile, menu.Rename)
        return menu
        
    def make_applications_menu(self, parent):
        """
        As the name implies, construct the applications menu and return it
        """
        menu = wx.Menu()
            
        apps_json_path = os.path.join(app_root_path, 'apps.json')
        if os.path.exists(apps_json_path):
            with open(apps_json_path, 'r') as fp:
                apps = json.load(fp)
                
            for app in apps:
                el = wx.MenuItem(menu, -1, app['name'], "", wx.ITEM_NORMAL)
                if wx_phoenix:
                    menu.Append(el)
                else:
                    menu.AppendItem(el)
                parent.Bind(wx.EVT_MENU, lambda evt, menu = el: parent.OnApplicationLaunch(evt, menu), el)
            self.apps = apps
        menu.Append(wx.MenuItem(menu, -1, "", "", wx.ITEM_SEPARATOR))
        menu.ModifyApplications = wx.MenuItem(menu, -1, "Modify...", "", wx.ITEM_NORMAL)
        menu.Append(menu.ModifyApplications)
        
        parent.Bind(wx.EVT_MENU, parent.OnModifyApplications, menu.ModifyApplications)
        
        return menu
        
    def make_menu_bar(self):
        """
        As the name implies, construct the menus and attach them all to the menubar
        """
        
        # Menu Bar
        self.menuBar = wx.MenuBar()

        # Build Run menu
        self.menuRun = wx.Menu()
        self.menuRunRun = wx.MenuItem(self.menuRun, -1, "&Run highlighted program", "", wx.ITEM_NORMAL)
        if wx_phoenix:
            self.menuRun.Append(self.menuRunRun)
        else:
            self.menuRun.AppendItem(self.menuRunRun)
        self.menuRunId = self.menuBar.Append(self.menuRun, "&Run")
        self.Bind(wx.EVT_MENU, lambda x, evt: x, self.menuRunRun)
        
        # Build File menu
        self.menuFile = self.make_file_menu(self)
        self.menuBar.Append(self.menuFile, "&File")
        
        # Build Directory menu
        self.menuDirectory = self.make_directory_menu(self)
        self.menuBar.Append(self.menuDirectory, "&Directory")
        
        # Build Application menu (empty to start)
        self.menuApplication = self.make_applications_menu(self)
        self.menuBar.Append(self.menuApplication, "&Application")
        
        # Build options menu
        self.menuOptions = self.make_options_menu(self)
        self.menuBar.Append(self.menuOptions, "&Options")
        
        # Exit menu
        self.menuExit = wx.Menu()
        self.menuExitExit = wx.MenuItem(self.menuExit, -1, "E&xit", "", wx.ITEM_NORMAL)
        if wx_phoenix:
            self.menuExit.Append(self.menuExitExit)
        else:
            self.menuExit.AppendItem(self.menuExitExit)
        self.menuBar.Append(self.menuExit, 'E&xit')
        
        #Actually set it
        self.SetMenuBar(self.menuBar)
        
if __name__=='__main__':    
    
    app = wx.App()
    
    if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
        frame = MainFrame(None, root_path = sys.argv[1])
    else:
        frame = MainFrame(None)
    
    frame.Show()
    
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()