#!/usr/bin/env python3

import wx
import datetime

class mainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(mainFrame, self).__init__(*args, **kw)
        big_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.todo_array = []
        self.current_todo_text = ""

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.panel = wx.Panel(self)
        self.panel.Bind(wx.EVT_LEFT_UP, self.onClick)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
        self.timer.Start(10000)


        self.current_todo = wx.TextCtrl(self.panel,style=wx.TE_PROCESS_ENTER)
        self.current_todo.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        self.current_todo.SetFont(big_font)
        self.current_todo.SetMargins((10,10))
        
        self.worked_on_this = wx.StaticText(self.panel, label="0 min", style=wx.ALIGN_CENTER)
        self.worked_on_this.SetFont(big_font)

        self.copyButton = wx.Button(self.panel, label="Copy")
        self.copyButton.Bind(wx.EVT_BUTTON, self.onCopyButton)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.Add(self.current_todo, wx.SizerFlags().Expand().Border(wx.ALL, 10))
        self.main_sizer.AddSpacer(20)
        self.main_sizer.Add(self.worked_on_this, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)
        self.main_sizer.AddSpacer(20)
        self.main_sizer.Add(self.copyButton, wx.SizerFlags().Expand().Border(wx.ALL, 10))



    def onEnter(self,event):
        now = datetime.datetime.now()
        if self.current_todo_text != self.current_todo.GetLineText(0):
            self.todo_array.append({'timestamp': now, 'todo_text': self.current_todo.GetLineText(0)})
            self.current_todo_text = self.current_todo.GetLineText(0)
            self.worked_on_this.SetLabel("0 min")
        event.Skip()

    def onCopyButton(self,event):
        now = datetime.datetime.now()
        out = "day\tstarttime\tendtime\tdelta\ttodo\r\n"
        first_flag = True
        start_timestamp = now
        last_todo = "nothing"
        for element in self.todo_array:
            if first_flag:
                start_timestamp = element['timestamp']
                last_todo = element['todo_text']
                first_flag = False
            else:
                day = element['timestamp'].strftime('%d')
                starttime = start_timestamp.strftime('%H%M')
                endtime = element['timestamp'].strftime('%H%M')
                delta = element['timestamp'] - start_timestamp
                todo = last_todo
                out += f"{day}\t{starttime}\t{endtime}\t{delta.total_seconds()/3600:.2f}\t{todo}\r\n"
                start_timestamp = element['timestamp']
                last_todo = element['todo_text']
        delta = now - start_timestamp
        out += f"{start_timestamp.strftime('%d')}\t{start_timestamp.strftime('%H%M')}\t{now.strftime('%H%M')}\t{delta.total_seconds()/3600:.2f}\t{last_todo}"
        if len(self.todo_array) == 0:
            dialogtext = 'No'
        else:
            dialogtext = f"{len(self.todo_array)}"
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(out))
                wx.TheClipboard.Close()

        dlg = wx.MessageDialog( self, f"{dialogtext} elements copied to clibboard", "Copy", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.
        event.Skip()

    def onClose(self,event):
        if event.CanVeto():
            if wx.MessageBox("Really?",
                            "Please confirm",
                            wx.ICON_QUESTION | wx.YES_NO) != wx.YES:
                event.Veto()
                return
        event.Skip()

    
    def onClick(self,event):
        self.current_todo.SetSelection(-1, -1)
        event.Skip()
    
    def onTimer(self,event):
        now = datetime.datetime.now()
        if len(self.todo_array) >0:
            start_last_event = self.todo_array[-1]['timestamp']
        else:
            start_last_event = now - datetime.timedelta(seconds=1)
        delta = now - start_last_event
        self.worked_on_this.SetLabel(f"{int(delta.total_seconds()/60)} min")
        event.Skip()

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    fOnTop = wx.STAY_ON_TOP or 0

    frm = mainFrame(None, title='I do this currently', style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN|fOnTop)
    frm.Show()
    app.MainLoop()