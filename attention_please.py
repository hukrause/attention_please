#!/usr/bin/env python3

import wx
import datetime
import pytz
import sqlite3
import platform
import os
import yaml

DB_VERSION = '0.1.0'

DB_INIT = """
CREATE TABLE version(id INTEGER PRIMARY KEY AUTOINCREMENT, 
version TEXT NOT NULL UNIQUE, 
deploy_time DATETIME);
INSERT INTO version VALUES (NULL,'0.1.0',DATETIME('now'));
CREATE TABLE time(id INTEGER PRIMARY KEY AUTOINCREMENT, 
timestamp DATETIME, 
todo_id INTEGER NOT NULL,
FOREIGN KEY(todo_id) REFERENCES todo(id));
CREATE TABLE todo(id INTEGER PRIMARY KEY AUTOINCREMENT, todo_text TEXT NOT NULL UNIQUE);
"""

SETTINGS_INIT = """
bg_color: [239,240,241]
"""

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

class Settings():
    def __init__(self):
        settings_path = self.__create_path()
        self.settings_file = os.path.join(settings_path,'settings.yml')
        default = yaml.safe_load(SETTINGS_INIT)
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as of:
                self.settings = default | yaml.safe_load(of)
        else:
            self.settings = default
        self.write_settings()

    def write_settings(self):
        with open(self.settings_file,'w') as of:
            yaml.dump(self.settings, of)

    def get(self,key):
        if key in self.settings:
            return self.settings[key]
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    
    def set(self,key,value):
        if key in self.settings:
            self.settings[key] = value
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __create_path(self):
        iam_running_on = platform.system()
        if iam_running_on == 'Linux':
            xdg_data_home = os.environ.get('$XDG_CONFIG_HOME',os.path.join(os.environ['HOME'],'.config'))
            path = os.path.join(xdg_data_home, 'attention_please')
        elif iam_running_on == 'Windows':
            path = os.path.join(os.environ['APPDATA'],'attention_please')
        # create path if not exists
        os.makedirs(path,exist_ok=True)
        return path

class Persistency():
    def __init__(self):
        dbpath = self.__create_path()
        self.con = sqlite3.connect(os.path.join(dbpath,'timeline.db'))
        self.cur = self.con.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON")
        self.cur.execute("PRAGMA case_sensitive_like=OFF")
        self.cur.arraysize = 100
        # initialize db as needed
        self.__init_db()

    def __init_db(self):
        res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='version'")
        if res.fetchone() is None:
            self.cur.executescript(DB_INIT)
            self.con.commit()
        else:
            res = self.cur.execute("SELECT version FROM version ORDER BY deploy_time DESC limit 1")
            if versiontuple(res.fetchone()[0]) < versiontuple(DB_VERSION):
                #TODO: implement run update script
                pass

    def get_known_todos(self):
        res = self.cur.execute("SELECT todo_text FROM todo ORDER by todo_text")
        todos = []
        for i in res.fetchall():
            todos.append(i[0])
        return todos

    def get_todo_array(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        todo_array = []
        res = self.cur.execute("SELECT ti.timestamp, t.todo_text FROM time as ti join todo as t ON t.id = ti.todo_id where ti.timestamp >= ?", [now])
        for i in res:
            timestamp = pytz.utc.localize(datetime.datetime.fromisoformat(i[0]))
            todo_array.append({'timestamp': timestamp, 'todo_text': i[1]})
        return todo_array

    def set_todo(self,todo_text):
        res = self.cur.execute("SELECT id FROM todo WHERE todo_text like ?",[todo_text])
        todo_id = res.fetchone()
        if todo_id is None:
            res = self.cur.execute("INSERT INTO todo VALUES (NULL, ?)",[todo_text])
            todo_id = self.cur.lastrowid
            self.con.commit()
        else:
            todo_id = todo_id[0]
        res = self.cur.execute("INSERT INTO time VALUES (NULL,DATETIME('now'),?)",[todo_id])
        self.con.commit()

    def __create_path(self):
        iam_running_on = platform.system()
        if iam_running_on == 'Linux':
            xdg_data_home = os.environ.get('$XDG_DATA_HOME',os.path.join(os.environ['HOME'],'.local/share'))
            path = os.path.join(xdg_data_home, 'attention_please')
        elif iam_running_on == 'Windows':
            path = os.path.join(os.environ['APPDATA'],'attention_please')
        # create path if not exists
        os.makedirs(path,exist_ok=True)
        return path

    def get_cur_todo(self):        
        res = self.cur.execute("SELECT a.todo_text FROM time AS t join todo AS a on t.todo_id = a.id ORDER BY t.timestamp DESC LIMIT 1")
        return res.fetchone()[0]


class mainPanel(wx.Panel):
    def __init__(self, *args, **kw):
        self.settings = kw.pop('settings',None)
        super(mainPanel, self).__init__(*args, **kw)
        self.parent = self.GetParent()
        big_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.save = Persistency()
        current_todo_text = self.save.get_cur_todo()

        self.worked_on_this = wx.StaticText(self, label=f"{('{: ^40}'.format(current_todo_text))}", style=wx.ALIGN_CENTER)
        self.worked_on_this.SetFont(big_font)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.worked_on_this,  1, wx.ALL | wx.EXPAND, border=5)
        self.setColor()
        self.SetSizer(self.main_sizer)
        
    def setTodo(self):
        current_todo_text = self.save.get_cur_todo()
        self.worked_on_this.SetLabel(f"{('{: ^40}'.format(current_todo_text))}")

    def setColor(self):
        self.worked_on_this.SetBackgroundColour(wx.Colour( self.settings.get('bg_color') ))

class controlPanel(wx.Panel):
    def __init__(self, *args, **kw):
        self.settings = kw.pop('settings',None)
        super(controlPanel, self).__init__(*args, **kw)
        self.parent = self.GetParent()
        self.save = Persistency()
        self.current_todo_text = self.save.get_cur_todo()
        self.elements_copied_up_to_now = 0
        if platform.system() == 'Windows':
            from tzlocal.win32 import get_localzone_name
            self.local = pytz.timezone(get_localzone_name())
        else:
            self.local = pytz.timezone(datetime.datetime.now().astimezone().tzname())

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
        self.timer.Start(10000)

        self.current_todo = wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER)
        self.current_todo.AutoComplete(self.save.get_known_todos())
        self.current_todo.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        
        self.worked_on_this_time = wx.StaticText(self, label="0 min", style=wx.ALIGN_CENTER)

        self.copyButton = wx.Button(self, label="Copy")
        self.copyButton.Bind(wx.EVT_BUTTON, self.onCopyButton)

        self.settingsButton = wx.Button(self, label="Settings")

        self.bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mid_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.mid_sizer.Add(self.current_todo, 1, wx.ALL | wx.EXPAND, border=5)
        
        self.bottom_sizer.Add(self.settingsButton,  1, wx.ALL | wx.EXPAND, border=1)
        self.bottom_sizer.Add(self.worked_on_this_time, 1, wx.ALL | wx.ALIGN_CENTER, border=5)
        self.bottom_sizer.Add(self.copyButton,  1, wx.ALL | wx.EXPAND, border=1)

        self.main_sizer.Add(self.mid_sizer,  1, wx.ALL | wx.EXPAND, border=1)
        self.main_sizer.Add(self.bottom_sizer,  1, wx.BOTTOM | wx.EXPAND, border=1)
        
        self.SetSizer(self.main_sizer)

    def onEnter(self,event):
        if self.current_todo_text != self.current_todo.GetLineText(0):
            self.current_todo_text = self.current_todo.GetLineText(0)
            self.save.set_todo(self.current_todo_text)
            self.worked_on_this_time.SetLabel("0 min")
            self.current_todo.AutoComplete(self.save.get_known_todos())
        event.Skip()

    def onCopyButton(self,event):
        now = datetime.datetime.now(datetime.timezone.utc)
        out = "day\tstarttime\tendtime\tdelta\ttodo\r\n"
        first_flag = True
        start_timestamp = now
        last_todo = "nothing"
        todo_array = self.save.get_todo_array()
        for element in todo_array:
            if first_flag:
                start_timestamp = element['timestamp']
                last_todo = element['todo_text']
                first_flag = False
            else:
                day = element['timestamp'].astimezone(self.local).strftime('%d')
                starttime = start_timestamp.astimezone(self.local).strftime('%H%M')
                endtime = element['timestamp'].astimezone(self.local).strftime('%H%M')
                delta = element['timestamp'] - start_timestamp
                todo = last_todo
                self.Layout()
                out += f"{day}\t{starttime}\t{endtime}\t{delta.total_seconds()/3600:.2f}\t{todo}\r\n"
                start_timestamp = element['timestamp']
                last_todo = element['todo_text']
        delta = now - start_timestamp
        out += f"{start_timestamp.astimezone(self.local).strftime('%d')}"
        out += f"\t{start_timestamp.astimezone(self.local).strftime('%H%M')}"
        out += f"\t{now.astimezone(self.local).strftime('%H%M')}"
        out += f"\t{delta.total_seconds()/3600:.2f}"
        out += f"\t{last_todo}"
        if len(todo_array) == 0:
            dialogtext = 'No'
        else:
            dialogtext = f"{len(todo_array)}"
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(out))
                wx.TheClipboard.Close()

        dlg = wx.MessageDialog( self, f"{dialogtext} elements copied to clibboard", "Copy", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.
        self.elements_copied_up_to_now = len(todo_array)
        event.Skip()
    
    def onTimer(self,event):
        now = datetime.datetime.now(datetime.timezone.utc)
        todo_array = self.save.get_todo_array()
        if len(todo_array) >0:
            start_last_event = todo_array[-1]['timestamp']
        else:
            start_last_event = now - datetime.timedelta(seconds=1)
        delta = now - start_last_event
        self.worked_on_this_time.SetLabel(f"{int(delta.total_seconds()/60)} min")
        self.Layout()
        event.Skip()

class settingsPanel(wx.Panel):
    def __init__(self, *args, **kw):
        self.settings = kw.pop('settings',None)
        super(settingsPanel, self).__init__(*args, **kw)
        self.parent = self.GetParent()
        self.visible = False
        
        # sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.bg_color_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # elemets
        self.color_picker = wx.ColourPickerCtrl(self, id=-1, colour=wx.RED,name="colourpicker",style=wx.CLRP_SHOW_LABEL|wx.CLRP_USE_TEXTCTRL)
        self.color_picker.Bind(wx.EVT_COLOURPICKER_CHANGED,self.onColorClick)

        self.bg_color_sizer.Add(self.color_picker,0,wx.ALL | wx.EXPAND, border=1)

        self.main_sizer.Add(self.bg_color_sizer,  1, wx.ALL | wx.EXPAND, border=1)
        self.SetSizer(self.main_sizer)
    
    def onColorClick(self,event):
        self.settings.set('bg_color',self.color_picker.GetColour())
        event.Skip()

class mainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(mainFrame, self).__init__(*args, **kw)
        self.settings = Settings()
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_ACTIVATE,self.onActivate)
        root = wx.Panel(self)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_panel = settingsPanel(root,settings=self.settings)
        self.main_panel = mainPanel(root,settings=self.settings)
        self.control_panel = controlPanel(root,settings=self.settings)

        self.control_panel.settingsButton.Bind(wx.EVT_BUTTON, self.onSettingsButton)

        self.main_sizer.Add(self.main_panel, 1, wx.EXPAND)
        self.main_sizer.Add(self.control_panel, 1, wx.EXPAND)
        self.main_sizer.Add(self.settings_panel, 1, wx.EXPAND)
        self.main_sizer.Hide(self.settings_panel)
        self.settings_visible = False
        root.Bind(wx.EVT_LEFT_UP, self.onClick)
        root.Bind(wx.EVT_TEXT_ENTER, self.onEnter)

        root.SetSizer(self.main_sizer)

        self.modSize()

    def onClick(self,event):
        self.controlPanel.current_todo.SetSelection(-1, -1)
        event.Skip()

    def onEnter(self,event):
        self.main_panel.setTodo()
        self.modSize()
        event.Skip()

    def onClose(self,event):
        if event.CanVeto():
            todo_array = self.main_panel.save.get_todo_array()
            if self.main_panel.elements_copied_up_to_now < len(todo_array):
                out = f"Do you want to close this App?\nThere are {len(todo_array) - self.main_panel.elements_copied_up_to_now} task(s) not copied up to now."
            else:
                out = "Do you want to close this App?"
            if wx.MessageBox(out,
                            "Please confirm",
                            wx.ICON_QUESTION | wx.YES_NO) != wx.YES:
                event.Veto()
                return
        event.Skip()

    def onActivate(self,event):
        if event.GetActive():
            self.main_sizer.Show(self.control_panel)
            if self.settings_visible:
                self.main_sizer.Show(self.settings_panel)
        else:
            self.main_sizer.Hide(self.control_panel)
            self.main_sizer.Hide(self.settings_panel)
        self.modSize()
        event.Skip()
    
    def onSettingsButton(self,event):
        if self.settings_visible:
            self.settings_visible = False
            self.main_sizer.Hide(self.settings_panel)
        else:
            self.settings_visible = True
            self.main_sizer.Show(self.settings_panel)
        self.modSize()
        event.Skip()

    def modSize(self):
        width_all = []
        height_all = []
        height = 0
        width = 0
        if self.settings_panel.IsShown():
            width_all.append(self.settings_panel.main_sizer.GetMinSize()[0])
            height_all.append(self.settings_panel.main_sizer.GetMinSize()[1])
        if self.control_panel.IsShown():
            width_all.append(self.control_panel.main_sizer.GetMinSize()[0])
            height_all.append(self.control_panel.main_sizer.GetMinSize()[1])
        
        width_all.append(self.main_panel.main_sizer.GetMinSize()[0])
        height_all.append(self.main_panel.main_sizer.GetMinSize()[1])
        
        for i in height_all:
            height += i
        width = max(width_all)
        print((width,height))
        self.main_sizer.SetMinSize((width,height))
        self.main_sizer.Fit(self)
        self.main_sizer.Layout()

if __name__ == '__main__':
    app = wx.App()
    fOnTop = wx.STAY_ON_TOP or 0

    frm = mainFrame(None, title='I do this currently', style=fOnTop)
    frm.Show()
    app.MainLoop()