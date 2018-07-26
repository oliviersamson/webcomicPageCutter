from tkinter import Tk, Label, Entry, IntVar, StringVar, OptionMenu, Button, messagebox, \
                    filedialog, colorchooser, TclError, Frame, LEFT, RIGHT, X
from PIL import Image
from threading import Thread, Lock

import itertools
import time
import numpy
import os

class DialogWindow:
    def __init__(self):
        self.window = Tk()
        self.window.title('Webcomic Page Cutter')
        self.window.resizable(0,0)

        self.background_color = self.window.cget('background')

        self.ask_color_frames_list = []
        self.ask_color_frames_nb = 0

        self.filenames = None
        self.result_directory = None
        self.split_colors = []

        self.mode = StringVar(self.window, 'Line average')
        self.threshold = IntVar(self.window, 10)
        self.min_nb_lines = IntVar(self.window, 50)
        self.min_height = IntVar(self.window, 3500)
        self.starting_number = IntVar(self.window, 1)
        self.format = StringVar(self.window, 'tif')

        vcmd = (self.window.register(self.validateEntry), '%P')

        ask_files_label = Label(self.window, text='File(s)', width=20, anchor='w')
        ask_files_label.grid(column=0, row=0, pady=10, padx=10, sticky='ew')
        self.files_label = Label(self.window, width=20, anchor='w')
        self.files_label.grid(column=1, row=0, pady=10, padx=10, sticky='ew')
        files_button = Button(self.window, text='Choose file(s)', command=self.askFilesNames)
        files_button.grid(column=2, row=0, pady=10, padx=10, sticky='ew')

        ask_directory_label = Label(self.window, text='Result directory', width=20, anchor='w')
        ask_directory_label.grid(column=0, row=1, pady=10, padx=10, sticky='ew')
        self.directory_label = Label(self.window, width=20, anchor='w')
        self.directory_label.grid(column=1, row=1, pady=10 ,padx=10, sticky='ew')
        directory_button = Button(self.window, text='Choose directory', command=self.askNewFilesDirectory)
        directory_button.grid(column=2, row=1, pady=10, padx=10, sticky='ew')

        ask_mode_label = Label(self.window, text='Cutting mode', width=20, anchor='w')
        ask_mode_label.grid(column=0, row=2, pady=10, padx=10, sticky='ew')
        self.mode_option_menu = OptionMenu(self.window, self.mode, *['Line average', 'Single pixels'])
        self.mode_option_menu.grid(column=2, row=2, pady=10, padx=8, sticky='ew')

        self.ask_color_frames = Frame(self.window, highlightthickness=0)
        self.ask_color_frames.grid(columnspan=3, pady=0, padx=0, sticky='ew')

        self.addAskColorFrame()

        color_button = Button(self.window, text='Add color', command=self.addAskColorFrame)
        color_button.grid(column=2, row=4, pady=10, padx=10, sticky='ew')

        ask_threshold_label = Label(self.window, text='Comparison threshold', width=20, anchor='w')
        ask_threshold_label.grid(column=0, row=5, pady=10, padx=10, sticky='ew')
        self.threshold_entry = Entry(self.window, textvariable=self.threshold, validate = 'key', \
            validatecommand = vcmd)
        self.threshold_entry.grid(column=2, row=5, pady=10, padx=10, sticky='ew')

        ask_min_nb_lines_label = Label(self.window, text='Min. # of lines for cut', width=20, anchor='w')
        ask_min_nb_lines_label.grid(column=0, row=6, pady=10, padx=10, sticky='ew')
        self.min_nb_lines_entry = Entry(self.window, textvariable=self.min_nb_lines, validate = 'key', \
            validatecommand = vcmd)
        self.min_nb_lines_entry.grid(column=2, row=6, pady=10, padx=10, sticky='ew')

        ask_min_height_label = Label(self.window, text='Min. page height', width=20, anchor='w')
        ask_min_height_label.grid(column=0, row=7, pady=10, padx=10, sticky='ew')
        self.min_height_entry = Entry(self.window, textvariable=self.min_height, validate = 'key', \
            validatecommand = vcmd)
        self.min_height_entry.grid(column=2, row=7, pady=10, padx=10, sticky='ew')

        ask_starting_nb_label = Label(self.window, text='Results starting #', width=20, anchor='w')
        ask_starting_nb_label.grid(column=0, row=8, pady=10, padx=10, sticky='ew')
        self.starting_nb_entry = Entry(self.window, textvariable=self.starting_number, validate = 'key', \
            validatecommand = vcmd)
        self.starting_nb_entry.grid(column=2, row=8, pady=10, padx=10, sticky='ew')

        ask_format_label = Label(self.window, text='Result format', width=20, anchor='w')
        ask_format_label.grid(column=0, row=9, pady=10, padx=10, sticky='ew')
        self.format_option_menu = OptionMenu(self.window, self.format, *['tif', 'jpg', 'png'])
        self.format_option_menu.grid(column=2, row=9, pady=10, padx=10, sticky='ew')

        start_button = Button(self.window, text='Start', command=self.onStart)
        start_button.grid(column=1, row=10, pady=10, padx=10, sticky='ew')

        cancel_button = Button(self.window, text='Cancel', command=self.close)
        cancel_button.grid(column=2, row=10, pady=10, padx=10, sticky='ew')

        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.window.mainloop()

    def onStart(self):
        if self.filenames == None or self.filenames == '':
            messagebox.showerror("Error", "No file(s) chosen")
            return

        if self.result_directory == None or self.result_directory == '':
            messagebox.showerror("Error", "No output directory chosen")
            return

        if self.split_colors == []:
            messagebox.showerror("Error", "No color chosen")
            return

        for split_color in self.split_colors:
            if split_color[1] == None or split_color[1] == (None, None):
                for index, ask_color_frame in enumerate(self.ask_color_frames.winfo_children()):
                    if ask_color_frame.winfo_id() == split_color[0]:
                        messagebox.showerror("Error", "No cutting color chosen for color #" + str(index + 1))
                        return

        if self.threshold_entry.get() == '':
            messagebox.showerror("Error", "No cutting threshold specified")
            return

        if self.min_nb_lines_entry.get() == '':
            messagebox.showerror("Error", "No min. # of lines for cut specified")
            return

        if self.min_height_entry.get() == '':
            messagebox.showerror("Error", "No min. page height specified")
            return

        if self.starting_nb_entry.get() == '':
            messagebox.showerror("Error", "No results starting # specified")
            return
        
        self.window.destroy()

    def close(self):
        self.window.destroy()
        exit(0)

    def addAskColorFrame(self):
        hex_vcmd = (self.window.register(self.validateHexEntry), '%P')

        ask_color_frame = Frame(self.ask_color_frames, highlightthickness=0)
        ask_color_frame.grid(columnspan=3, pady=0, padx=0, sticky='ew')

        ask_color_label = Label(ask_color_frame, text='Cutting color #' + str(self.ask_color_frames_nb + 1), width=20, anchor='w')
        ask_color_label.pack(side=LEFT, pady=10, padx=10)
        color_label = Label(ask_color_frame, width=15, anchor='w')
        color_label.pack(side=LEFT, pady=10, padx=5)
        color_hex_entry = Entry(ask_color_frame, validate = 'key', validatecommand = hex_vcmd)
        color_hex_entry.insert(0, '0f0f0f')
        color_hex_entry.bind('<FocusIn>', lambda _: self.on_color_hex_entry_click(None, ask_color_frame))
        color_hex_entry.bind('<FocusOut>', lambda _: self.on_color_hex_focusout(None, ask_color_frame))
        color_hex_entry.pack(side=LEFT, pady=10, padx=18)
        color_hex_entry.config(width=6, fg='gray')
        color_button = Button(ask_color_frame, text='X', width=3,\
            command=lambda:(self.deleteSplitColor(ask_color_frame.winfo_id()) if self.ask_color_frames_nb != 1 else None, \
            self.deleteAskColorFrame(ask_color_frame)))
        color_button.pack(side=RIGHT, pady=10, padx=10)
        color_button = Button(ask_color_frame, text='Pick color', command=lambda: self.askSplitColor(ask_color_frame))
        color_button.pack(side=LEFT, pady=10, padx=0)   
        color_button.config(width=12)

        self.ask_color_frames_nb = self.ask_color_frames_nb + 1

    def deleteAskColorFrame(self, frame):
        if self.ask_color_frames_nb != 1:
            frame.destroy()
            frame = None

            self.ask_color_frames_nb = self.ask_color_frames_nb - 1

            self.updateAskColorLabelsNb()
        else:
            messagebox.showerror("Error", "Cannot delete the remaining color widget")

    def addSplitColor(self, frame_id, color):
        already_exists = False
        for index, split_color in enumerate(self.split_colors):
            if split_color[0] == frame_id:
                self.split_colors[index] = (split_color[0], color)
                already_exists = True

        if not already_exists:
            self.split_colors.append((frame_id, color))

    def deleteSplitColor(self, frame_id):
            try:
                self.split_colors.remove(next(split_color for split_color in self.split_colors if split_color[0] == frame_id))
            except StopIteration:
                pass

    def updateAskColorLabelsNb(self):
        for index, ask_color_frame in enumerate(self.ask_color_frames.winfo_children()):
            ask_color_frame.winfo_children()[0].config(text='Cutting color #' + str(index + 1))

    def askFilesNames(self):
        self.filenames = filedialog.askopenfilenames()
        self.files_label.config(text='{} file(s) chosen' .format(len(self.filenames)))

    def askNewFilesDirectory(self):
        self.result_directory = filedialog.askdirectory()
        self.directory_label.config(text='{}' .format(self.result_directory))

    def askSplitColor(self, ask_color_frame):
        color = colorchooser.askcolor()

        self.addSplitColor(ask_color_frame.winfo_id(), color)
        
        if color != None and color != (None, None):
            ask_color_frame.winfo_children()[2].delete(0, "end")
            ask_color_frame.winfo_children()[2].insert(0, color[1][1:])
            ask_color_frame.winfo_children()[2].config(fg = 'black')
            
            ask_color_frame.winfo_children()[1].config(background='{}' .format(color[1]))

    def validateEntry(self, text):
        if str.isdigit(text) or text == '':
            return True
        else:
            return False

    def validateHexEntry(self, text):
        valid_hex_char = lambda c: c in 'abcdef0123456789'
        return (len(text) < 7) and (all(valid_hex_char(z) for z in text.lower()))

    def on_color_hex_entry_click(self, event, ask_color_frame):
        if ask_color_frame.winfo_children()[2].cget('fg') == 'gray':
            ask_color_frame.winfo_children()[2].delete(0, "end")
            ask_color_frame.winfo_children()[2].insert(0, '')
            ask_color_frame.winfo_children()[2].config(fg = 'black')
        
        elif ask_color_frame.winfo_children()[2].cget('fg') == 'red':
            ask_color_frame.winfo_children()[2].config(fg = 'black')
    
    def on_color_hex_focusout(self, event, ask_color_frame):
        if ask_color_frame.winfo_children()[2].get() == '':
            ask_color_frame.winfo_children()[2].insert(0, '0f0f0f')
            ask_color_frame.winfo_children()[2].config(fg = 'gray')

            self.deleteSplitColor(ask_color_frame.winfo_id())

            ask_color_frame.winfo_children()[1].config(background=self.background_color)

        elif len(ask_color_frame.winfo_children()[2].get()) < 6:
            ask_color_frame.winfo_children()[2].config(fg = 'red')

            self.deleteSplitColor(ask_color_frame.winfo_id())

            ask_color_frame.winfo_children()[1].config(background=self.background_color)

        elif len(ask_color_frame.winfo_children()[2].get()) == 6:
            hex_color = ask_color_frame.winfo_children()[2].get()
            color = ((int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)), '#' + hex_color)

            self.addSplitColor(ask_color_frame.winfo_id(), color)

            ask_color_frame.winfo_children()[1].config(background='{}' .format(color[1]))

def isWithinSplitColorThreshold(pixel, split_color, split_color_threshold):
    if abs(int(pixel[0]) - int(split_color[0][0])) < split_color_threshold and \
    abs(int(pixel[1]) - int(split_color[0][1])) < split_color_threshold and \
    abs(int(pixel[2]) - int(split_color[0][2])) < split_color_threshold:
        return True
    else:
        return False

def cutPages(filenames, result_directory, comparison_mode, split_colors, split_color_threshold, \
    min_nb_lines, min_height, start_nb, result_format):
    
    if len(filenames) == 1:
        image = Image.open(filenames[0])
        image_array = numpy.array(image)
        
    elif len(filenames) != 0:
        partial_images = [Image.open(filename) for filename in filenames]
        image_array = numpy.vstack((numpy.asarray(partial_image) for partial_image in partial_images))

    else:
        exit(0)

    same_color_lines = []
    cutting_points = []
    cutting_points.append(0)
    last_cutting_point = 0

    for index, image_line in enumerate(image_array):
        uniform_split_color_area = False
        if comparison_mode == 'Single pixels':
            for split_color in split_colors:
                if all(isWithinSplitColorThreshold(pixel, split_color[1], split_color_threshold) \
                for pixel in image_line):

                    same_color_lines.append(index)
                    uniform_split_color_area = True
        else:
            line_average = numpy.mean(image_line, axis=0)
            for split_color in split_colors:
                if isWithinSplitColorThreshold(line_average, split_color[1], split_color_threshold):

                    same_color_lines.append(index)
                    uniform_split_color_area = True

        if not uniform_split_color_area:
            if len(same_color_lines) > min_nb_lines:
                current_cutting_point = numpy.median(same_color_lines)
                if (current_cutting_point - last_cutting_point) > min_height:
                    cutting_points.append(current_cutting_point)
                    last_cutting_point = current_cutting_point
            
            same_color_lines = []

    cutting_points.append(len(image_array))

    sliced_images = []

    for previous_cutting_point, cutting_point in zip(cutting_points, cutting_points[1:]):
        sliced_image_array = image_array[int(previous_cutting_point): int(cutting_point)]
        sliced_images.append(Image.fromarray(sliced_image_array))

    for index, sliced_image in enumerate(sliced_images):
        file = open(os.path.join(result_directory, "{}.{}" .format(index + start_nb, result_format)), mode='w+b')
        sliced_image.save(file, dpi=(72, 72))
        file.close

class LoadingWindow:
    def __init__(self):
        self.loading_dots_gen = self.loadingDotsGenerator()

        self.window = Tk()

        self.loading_label = Label(self.window, width=20, anchor='w')
        self.loading_label.grid(column=1, row=0, pady=10, padx=10, sticky='ew')

        cancel_button = Button(self.window, text='Cancel', command=self.close)
        cancel_button.grid(column=2, row=1, pady=10, padx=10, sticky='ew')

        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.update()

    def close(self):
        self.window.after_cancel(self.after_id)
        self.window.destroy()

    def loadingDotsGenerator(self):
        for loading_dots in itertools.cycle(['.', '..', '...']):
            yield loading_dots

    def update(self):
        self.loading_label.config(text='Processing {}' .format(next(self.loading_dots_gen)))

        self.after_id = self.window.after(500, self.update)

def main():
    dialog_window = DialogWindow()

    start_time = time.time()

    processing_thread = Thread(target=cutPages, args=[dialog_window.filenames, dialog_window.result_directory, \
        dialog_window.mode.get(), dialog_window.split_colors, dialog_window.threshold.get(), dialog_window.min_nb_lines.get(), \
        dialog_window.min_height.get(), dialog_window.starting_number.get(), dialog_window.format.get()], daemon=True)
    
    processing_thread.start()

    loading_window = LoadingWindow()
    
    while processing_thread.is_alive():
        try:
            loading_window.window.update_idletasks()
            loading_window.window.update()
            time.sleep(0.01)
        except TclError:
            return

    loading_window.close()

    end_time = time.time()
    print('Processing time : {} s' .format(end_time - start_time))

if __name__ == '__main__':
    main()