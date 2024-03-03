#!/usr/bin/env python3

import wx
import datetime
import sqlite3
import platform
import os

class persistency():
    def __init__(self):
        dbpath = self.__create_db_path()
        self.datacon = sqlite3.connect(os.path.join(dbpath,'timeline.db'))
        self.datacur = self.datacon.cursor()
        # initialize db as needed
        self.__init_data_db()

    def __init_data_db(self):
        res = datacur.execute("SELECT name FROM sqlite_master WHERE name='version'")
        if res.fetchone() is None:
            pass
            


    def __create_db_path(self):
        iam_running_on = platform.system()
        if iam_running_on == 'Linux':
            xdg_data_home = os.environ.get('XDG_DATA_HOME',os.path.join(os.environ['HOME'],'.local', 'share'))
            path = os.path.join(xdg_data_home, 'attention_please')
        elif iam_running_on == 'Windows':
            path = os.path.join(os.environ['APPDATA'],'attention_please')
        # create path if not exists
        os.makedirs(path)
        return path


class mainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(mainFrame, self).__init__(*args, **kw)
        big_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.todo_array = []
        self.current_todo_text = ""
        self.elements_copied_up_to_now = 0

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.panel = wx.Panel(self)
        self.panel.Bind(wx.EVT_LEFT_UP, self.onClick)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
        self.timer.Start(10000)


        self.current_todo = wx.TextCtrl(self.panel,style=wx.TE_PROCESS_ENTER)
        self.current_todo.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        
        self.worked_on_this = wx.StaticText(self.panel, label=f"{self.current_todo_text}\n0 min", style=wx.ALIGN_CENTER)
        self.worked_on_this.SetFont(big_font)
        self.worked_on_this.Bind(wx.EVT_LEFT_UP, self.onClick)

        self.copyButton = wx.Button(self.panel, label="Copy")
        self.copyButton.Bind(wx.EVT_BUTTON, self.onCopyButton)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.Add(self.current_todo, wx.SizerFlags().Expand().Border(wx.ALL, 10))
        self.main_sizer.Add(self.worked_on_this, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)
        self.main_sizer.Add(self.copyButton, wx.SizerFlags().Expand().Border(wx.ALL, 10))



    def onEnter(self,event):
        now = datetime.datetime.now()
        if self.current_todo_text != self.current_todo.GetLineText(0):
            self.todo_array.append({'timestamp': now, 'todo_text': self.current_todo.GetLineText(0)})
            self.current_todo_text = self.current_todo.GetLineText(0)
            self.worked_on_this.SetLabel(f"{self.current_todo_text}\n0 min")
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
        self.elements_copied_up_to_now = len(self.todo_array)
        event.Skip()

    def onClose(self,event):
        if event.CanVeto():
            if self.elements_copied_up_to_now < len(self.todo_array):
                out = f"Do you want to close this App?\nThere are {len(self.todo_array) - self.elements_copied_up_to_now} task(s) not copied up to now."
            else:
                out = "Do you want to close this App?"
            if wx.MessageBox(out,
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
        self.worked_on_this.SetLabel(f"{self.current_todo_text}\n{int(delta.total_seconds()/60)} min")
        event.Skip()

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    fOnTop = wx.STAY_ON_TOP or 0

    frm = mainFrame(None, title='I do this currently', style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN|fOnTop)
    frm.Show()
    app.MainLoop()