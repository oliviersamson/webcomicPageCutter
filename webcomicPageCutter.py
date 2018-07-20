from tkinter import Tk, Label, Entry, IntVar, Toplevel, StringVar, OptionMenu, Button, messagebox, \
                    simpledialog, filedialog, colorchooser, TclError, Frame, LEFT, RIGHT, TOP, X, Y
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

        self.ask_color_frames_nb = 0

        self.filenames = None
        self.result_directory = None
        self.split_color = None

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
        self.mode_option_menu.grid(column=2, row=2, pady=10, padx=10, sticky='ew')

        self.ask_color_frames = Frame(self.window, highlightthickness=0)
        self.ask_color_frames.grid(columnspan=3, pady=0, padx=0, sticky='ew')

        self.addAskColorFrame()

        '''
        ask_color_label = Label(self.ask_color_frames, text='Cutting color', width=20, anchor='w')
        ask_color_label.pack(side=LEFT, pady=10, padx=10)
        self.color_label = Label(self.ask_color_frames, width=20, anchor='w')
        self.color_label.pack(side=LEFT, pady=10, padx=10)
        color_button = Button(self.ask_color_frames, text='Choose color', command=lambda: self.askSplitColor(self.ask_color_frames_nb))
        color_button.pack(side=LEFT, pady=10, padx=10, expand=True, fill=X)
        '''

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

        if self.split_color == None or self.split_color == (None, None):
            messagebox.showerror("Error", "No cutting color chosen")
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
        ask_color_frame = Frame(self.ask_color_frames, highlightthickness=0)
        ask_color_frame.grid(columnspan=3, row=self.ask_color_frames_nb, pady=0, padx=0, sticky='ew')

        ask_color_label = Label(ask_color_frame, text='Cutting color', width=20, anchor='w')
        ask_color_label.pack(side=LEFT, pady=10, padx=10)
        color_label = Label(ask_color_frame, width=20, anchor='w')
        color_label.pack(side=LEFT, pady=10, padx=10)
        color_button = Button(ask_color_frame, text='Choose color', \
            command=lambda: self.askSplitColor(self.ask_color_frames_nb, color_label))
        color_button.pack(side=LEFT, pady=10, padx=10, expand=True, fill=X)

        self.ask_color_frames_nb = self.ask_color_frames_nb + 1

    def askFilesNames(self):
        self.filenames = filedialog.askopenfilenames()
        self.files_label.config(text='{} file(s) chosen' .format(len(self.filenames)))

    def askNewFilesDirectory(self):
        self.result_directory = filedialog.askdirectory()
        self.directory_label.config(text='{}' .format(self.result_directory))

    def askSplitColor(self, index, color_label):
        self.split_color = colorchooser.askcolor()
        if self.split_color != None and self.split_color != (None, None):
            color_label.config(background='{}' .format(self.split_color[1]))

    def validateEntry(self, text):
        if str.isdigit(text) or text == '':
            return True
        else:
            return False

def isWithinSplitColorThreshold(pixel, split_color, split_color_threshold):
    if abs(int(pixel[0]) - int(split_color[0][0])) < split_color_threshold and \
    abs(int(pixel[1]) - int(split_color[0][1])) < split_color_threshold and \
    abs(int(pixel[2]) - int(split_color[0][2])) < split_color_threshold:
        return True
    else:
        return False

def cutPages(filenames, result_directory, comparison_mode, split_color, split_color_threshold, \
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
            if all(isWithinSplitColorThreshold(pixel, split_color, split_color_threshold) \
            for pixel in image_line):

                same_color_lines.append(index)
                uniform_split_color_area = True
        else:
            line_average = numpy.mean(image_line, axis=0)
            if isWithinSplitColorThreshold(line_average, split_color, split_color_threshold):

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
        dialog_window.mode.get(), dialog_window.split_color, dialog_window.threshold.get(), dialog_window.min_nb_lines.get(), \
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