# Attention\_Please

The purpose of this tool is to display the current work topic and measure the time the topic has taken. It should be easy to use, just a text field and the time this topic has taken so far. The most important thing is that this tool is always in the foreground. The reason for this is that I would like to know what the current task is.

This tool is an early alpha version.

## install

Make sure that wxpython at least in version 4.2 is installed. To do this on Debian and Ubuntu:

```bash
sudo apt install python3-wxgtk4.0
```

Then ist should be possible to start the executable `attention_please.py`. On Windows or other OS you are at your own at the moment. The Only real dependency is a working wxpython installation with python 3.11 or higher. I've testet it on Debian 12 with wxpython 4.2.0.

## Usage

After starting, enter a text describing what you are doing (for example, a ticket number). Finish your entry with a new line to start the time measurement. If you click on the background of the window, you can select the entered text and change the task again, all other editing options are of course also available. Press "Return" again to start the time measurement. If you want to exit the programme, you can do so by closing the window. You will be asked for confirmation. The measured time can be copied to the clipboard using the copy button. Paste this text into a text editor or spreadsheet of your choice. There is no persistence, when the programme is closed, all data is deleted.

## Output

After you have copied the data into the clipboard, a tsv formatted table is available. It has the following format:

```
day: the current day as number
starttime: The time when this todo was startet as HHMM string
endtime: The Time when this todo has ended as HHMM string
delta: A floating point number rounded to two decimal places with the hours that this todo has taken
todo: The string that was given for this todo
```