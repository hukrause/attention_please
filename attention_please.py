# First things, first. Import the wxPython package.
import wx
import datetime

class mainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(mainFrame, self).__init__(*args, **kw)

        self.panel = mainPanel(self)
        self.textField = wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.enterPressed, self.textField)
        self.worked_on_this = wx.StaticText(self.panel, label="0", style=wx.ALIGN_CENTER)
        big_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.worked_on_this.SetFont(big_font)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)
        self.create_layout()


    def create_layout(self):
        # Add the text control to the top box
        self.main_sizer.Add(self.textField, 1, wx.EXPAND | wx.ALL, border=10)
        
        # Add some space between the two boxes
        self.main_sizer.AddSpacer(20)
        
        # Add the static text to the bottom box
        self.main_sizer.Add(self.worked_on_this, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

    def enterPressed(self,event):
        now = datetime.datetime.now()
        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')};{self.textField.GetLineText(0)}")

class mainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)



if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    fOnTop = wx.STAY_ON_TOP or 0

    frm = mainFrame(None, title='Hello World 2', style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN|fOnTop)
    frm.Show()
    app.MainLoop()