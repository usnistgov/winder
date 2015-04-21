import wx

try:
    import wx.gizmos as gizmos
    
    class TreeListCtrl(gizmos.TreeListCtrl):
        """
        This class implements the functions of the new Phoenix interface
        using the classic TreeListCtrl api, in order to make the transition between 
        them as seamless as possible
        """
        
        def AppendColumn(self, colname, **kwargs):
            # classic style
            if 'align' in kwargs:
                kwargs['flag'] = kwargs.pop('align')
            self.AddColumn(colname, **kwargs)
            
        def AppendItem(self, parent, text, imageClosed, imageOpened):
            # classic style
            child = gizmos.TreeListCtrl.AppendItem(self, parent, text)
            self.SetItemImage(child, imageClosed, which = wx.TreeItemIcon_Normal)
            self.SetItemImage(child, imageOpened, which = wx.TreeItemIcon_Expanded)
            return child
        
        def SetItemText(self, item, col, value):
            child = gizmos.TreeListCtrl.SetItemText(self, item, value, col)
            
        def FillColumn(self, index, value):
            item = self.GetRootItem()
            while item.IsOk():
                self.SetItemText(item,value,index)
                item = self.GetNextItem(item)
        
        def GetNextItem(self, item):
            return self.GetNext(item) # GetNextItem in wxwidgets - why was it called GetNext in wxpython?
                
        def GetFirstChild(self, item):
            item, junk = gizmos.TreeListCtrl.GetFirstChild(self, item)
            return item
            
        def ClearColumns(self):
            while self.GetColumnCount() > 0:
                self.RemoveColumn(0)
except ImportError:
    from wx.dataview import TreeListCtrl