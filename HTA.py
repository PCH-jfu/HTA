import tkinter as tk
import serial
import csv
import threading
import queue
import datetime
import serial.tools.list_ports
import sys

__author__ = "Justin Fu"
__copyright__ = "Copyright 2018, The Helios Testing Script"
__version__ = "0.1.8"
__email__ = "justin.fu@pchintl.com"



class SerialThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.shutdown_flag = threading.Event()
        self.reset_flag = threading.Event()
        self.ports = list(serial.tools.list_ports.comports())
        if not self.ports:
            sys.exit()
        for p in self.ports:
            if 'MSP430' in str(p):
                self.port_name = p.device
                break
            else:
                sys.exit()
        
    def run(self):
        ser = serial.Serial(self.port_name, 9600, timeout=0.1)
        self.clear_queue = 0
        self.count = 0
        self.uid_detect = False
        while True:
            
            # this loop is break only when 
            while True:
                # check if close button is press
                if self.shutdown_flag.is_set():
                    return
                # check if reset button is press
                elif self.reset_flag.is_set():
                    # clear everything in this thread
                    self.uid_detect = False
                    self.count = 0
                    while self.queue.qsize():
                        try:
                            print("queue clean")
                            self.queue.get(self.clear_queue)
                        except queue.Empty:
                            pass
                    # clear reset flag
                    self.reset_flag.clear()

                # read a line from serial port    
                self.read_out = ser.readline().decode('latin1')
                    
                if "UID:" in self.read_out and not self.uid_detect:
                    self.send = "UID: " + self.read_out[self.read_out.find('[')+1: self.read_out.find(']')]
                    self.queue.put(self.send)
                    print(self.send)
                    self.uid_detect = True
                    self.count = 0

                elif "Block 04 Data:" in self.read_out and self.count < 20 and self.uid_detect:
                    self.adc_start = self.read_out.find('[')+5
                    self.send = "ADC: " + self.read_out[self.adc_start+2: self.adc_start+4] + self.read_out[self.adc_start: self.adc_start+2]
                    self.queue.put(self.send)
                    print(self.send)
                    self.count += 1
                    
                ser.flush()



class  Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.create_widgets()
        
        master.protocol("WM_DELETE_WINDOW", self.close)

        self.queue = queue.Queue()
        self.thread = SerialThread(self.queue)
        self.thread.start()
        self.button_pressed = False

    def create_widgets(self):

        # Display UID
        self.uid_frame = tk.Frame(self, relief="raised", borderwidth=1)
        self.uid_frame.pack(fill = "x")

        self.uid_label = tk.Label(self.uid_frame, text="UID: ", font=("Counrier", 25))
        self.uid_label.pack(side="left", padx=10, pady=10)
        
        self.uid_text = tk.Entry(self.uid_frame, font=("Counrier, 25"), bg="light gray")
        self.uid_text.pack(fill="both", padx=10, pady=10, expand=True)

        # The first test
        self.test1_frame = tk.Frame(self, relief="raised", borderwidth=1)
        self.test1_frame.columnconfigure(0, pad=10, weight=1, uniform="four")
        self.test1_frame.columnconfigure(1, pad=10, weight=1, uniform="four")
        self.test1_frame.columnconfigure(2, pad=10, weight=1, uniform="four")
        self.test1_frame.columnconfigure(3, pad=10, weight=1, uniform="four")
        self.test1_frame.columnconfigure(4, pad=10, weight=1, uniform="four")
        self.test1_frame.rowconfigure(0, pad = 10)
        self.test1_frame.pack(fill = "x")

        self.test1_button = tk.Button(self.test1_frame)
        self.test1_button["text"] = "Test 1"
        self.test1_button["command"] = self.test1_call
        self.test1_button["font"] = ("Counrier", 25)
        self.test1_button.grid(row=0, column=0)
       
        self.avg_adc = tk.Text(self.test1_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.avg_adc.grid(row=0, column=2)
        
        self.result1_frame = tk.Frame(self.test1_frame, relief="raised", borderwidth=1)
        self.result1_frame.grid(row=0, column=4, sticky="w"+"e"+"n"+"s")
        self.origin_color = self.result1_frame.cget("background")

        self.result1_label = tk.Label(self.result1_frame, font=("Counrier", 25))
        self.result1_label.pack(fill="none", expand=True)

        # The second test
        self.test2_frame = tk.Frame(self, relief="raised", borderwidth=1)
        self.test2_frame.columnconfigure(0, pad=10, weight=1, uniform="four")
        self.test2_frame.columnconfigure(1, pad=10, weight=1, uniform="four")
        self.test2_frame.columnconfigure(2, pad=10, weight=1, uniform="four")
        self.test2_frame.columnconfigure(3, pad=10, weight=1, uniform="four")
        self.test2_frame.columnconfigure(4, pad=10, weight=1, uniform="four")
        self.test2_frame.rowconfigure(0, pad=10)
        self.test2_frame.pack(fill="x")
        
        self.test2_button = tk.Button(self.test2_frame, text="Test 2", font=("Counrier, 25"), command=self.test2_call)
        self.test2_button.grid(row=0, column=0)

        self.test2_dmm = tk.Text(self.test2_frame, height=1, width=6, font=("Counrier, 25"))
        self.test2_dmm.grid(row = 0, column=1)

        self.charged_adc = tk.Text(self.test2_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.charged_adc.grid(row=0, column=2)
        
        self.discharged_adc = tk.Text(self.test2_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.discharged_adc.grid(row=0, column=3)
        
        self.result2_frame = tk.Frame(self.test2_frame, relief="raised", borderwidth=1)
        self.result2_frame.grid(row=0, column=4, sticky="w"+"e"+"n"+"s")

        self.result2_label = tk.Label(self.result2_frame, font=("Counrier", 25))
        self.result2_label.pack(fill="none", expand=True)

        # Control button
        self.control_frame = tk.Frame(self, relief="raised", borderwidth=1)
        self.control_frame.columnconfigure(0, pad=10, weight=1, uniform="four")
        self.control_frame.columnconfigure(1, pad=10, weight=1, uniform="four")
        self.control_frame.columnconfigure(2, pad=10, weight=1, uniform="four")
        self.control_frame.columnconfigure(3, pad=10, weight=1, uniform="four")
        self.control_frame.columnconfigure(4, pad=10, weight=1, uniform="four")
        self.control_frame.rowconfigure(0, pad=10)
        self.control_frame.pack(fill="x")

        self.quit = tk.Button(self.control_frame, text="Close", fg="red", command=self.close, font=("Counrier, 25"))
        self.quit.grid(row=0, column=4)
        
        self.reset = tk.Button(self.control_frame, text="Reset", command=self.reset, font=("Counrier, 25"))
        self.reset.grid(row=0, column=3)

        self.version_label = tk.Label(self, text="Version: "+__version__)
        self.version_label.pack(side="right", padx=10, pady=10)
        
    # Test1 button callback function
    def test1_call(self):
        print("Test1 Button Pressed!")
        if not self.button_pressed:
            self.button_pressed = True
            self.process_queue(21)
    
    # Test2 button callback function
    def test2_call(self):
        print("Test2 Button Pressed!")

        if not self.button_pressed:
            self.button_pressed = True
            self.process_queue(3)

    def retrieve_dmm(self):
        dmm_value = self.test2_dmm.get("1.0", "end")
        dmm_value = dmm_value.split()

        if len(dmm_value):
            dmm_value = dmm_value[0]
        else:
            dmm_value = "no value"

        if self.is_int_or_float(dmm_value):
            dmm_voltage = float(dmm_value)
        else:
            dmm_voltage = -1
        print(dmm_voltage)
        return dmm_voltage
            
    def is_int_or_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False



    def process_queue(self, item):
        if self.queue.qsize() < item and self.button_pressed:
            self.uid_text.insert("0", ".")
            root.after(1000, self.process_queue, item)
        elif self.queue.qsize() >= item and self.button_pressed:
            if item == 21:
                uid, adc = self.adc_process10()
                voltage = self.adc_calculate(adc)

                self.uid_text.delete(0, "end")
                self.uid_text.insert(0, uid)
                self.avg_adc.delete("0.0", "end")
                self.avg_adc.insert("0.0", voltage)
                if voltage < 5:
                    self.show_result(1, True)
                    self.record_result(1, uid, "pass", voltage)
                else:
                    self.show_result(1, False)
                    self.record_result(1, uid, "fail", voltage)

            elif item == 3:
                target_voltage = 18
                tolerance_dmm = 3.5
                tolerance_target = 5

                dmm_voltage = self.retrieve_dmm()
                uid, adc1, adc2 = self.adc_process2()
                voltage1 = self.adc_calculate(adc1)
                voltage2 = self.adc_calculate(adc2)

                self.uid_text.delete(0, "end")
                self.uid_text.insert(0, uid)
                self.charged_adc.delete("0.0", "end")
                self.charged_adc.insert("0.0", voltage1)
                self.discharged_adc.delete("0.0", "end")
                self.discharged_adc.insert("0.0", voltage2)
              
                # Test criteria
                if abs(voltage1-dmm_voltage) > tolerance_dmm and dmm_voltage != -1:
                    test_pass = False
                    print("error 1: DMM not match")
                    self.record_result(2, uid, "error1", voltage1, voltage2, dmm_voltage)
                elif abs(dmm_voltage-target_voltage) > tolerance_target:
                    test_pass = False
                    print("error 4: target voltage(DMM) not match")
                    self.record_result(2, uid, "error4", voltage1, voltage2, dmm_voltage)
                elif abs(voltage1-target_voltage) > tolerance_target:
                    test_pass = False
                    print("error 2: target voltage not match")
                    self.record_result(2, uid, "error2", voltage1, voltage2, dmm_voltage)
                elif voltage2 > 5:
                    test_pass = False
                    print("error 3: target voltage not match")
                    self.record_result(2, uid, "error3", voltage1, voltage2, dmm_voltage)
                else:
                    test_pass = True    
                    self.record_result(2, uid, "pass", voltage1, voltage2, dmm_voltage)

                if test_pass: 
                    self.show_result(2, True)
                else:
                    self.show_result(2, False)
        else:
            pass
    
    def show_result(self, test, result):
        if test == 1 and result == True:
            self.result1_frame.configure(background="green")
            self.result1_label.configure(text="PASS", background="green")
        elif test == 1 and result == False:
            self.result1_frame.configure(background="red")
            self.result1_label.configure(text="FAIL", background="red")
        elif test == 2 and result == True:
            self.result2_frame.configure(background="green")
            self.result2_label.configure(text="PASS", background="green")
        elif test == 2 and result == False:
            self.result2_frame.configure(background="red")
            self.result2_label.configure(text="FAIL", background="red")
        else:
            pass

    def clean_result(self):
        self.result1_frame.configure(background=self.origin_color)
        self.result1_label.configure(text=" ", background=self.origin_color)
        self.result2_frame.configure(background=self.origin_color)
        self.result2_label.configure(text=" ", background=self.origin_color)

    def adc_process10(self):
        adc_sum = 0
        for item in range(0, 21):                       # increase the number of messages to 21
            try:
                receive = self.queue.get()
                if "UID: " in receive:
                    uid = receive.strip("UID: ")
                elif "ADC: " in receive and item > 11:  # get the value in message 12-21
                    adc = int(receive.strip("ADC: "), 16)
                    adc_sum = adc_sum + adc
                print(item)
            except queue.Empty:
                pass
        adc_value = adc_sum / 10
        return uid, adc_value
        
    def adc_process2(self):
        adc1 = 0
        adc2 = 0
        for item in range(0, 3):
            try:
                receive = self.queue.get()
                if "UID: " in receive:
                    uid = receive.strip("UID: ")
                elif "ADC: " in receive and adc1 == 0:
                    adc1 = int(receive.strip("ADC: "), 16)
                elif "ADC: " in receive:
                    adc2 = int(receive.strip("ADC: "), 16)
                print(item)
            except queue.Empty:
                pass
        return uid, adc1, adc2


    def adc_calculate(self, adc):
        voltage = round(adc*0.9/16383/2*1000, 2)
        return voltage
    

    # shutdown button callback
    def close(self):
        self.thread.shutdown_flag.set()
        self.thread.join()
        root.destroy()
    
    # reset button callback
    def reset(self):
        self.uid_text.delete(0, "end")
        self.avg_adc.delete("0.0", "end")
        self.charged_adc.delete("0.0", "end")
        self.discharged_adc.delete("0.0", "end")
        self.test2_dmm.delete("0.0", "end")
        self.clean_result()
        self.thread.reset_flag.set()
        self.button_pressed = False

    # Record result
    def record_result(self, test, uid, result, value1, value2=None, value3=None):
        if test == 1:
            with open('Test1.csv', 'a', newline='') as test1file:
                fieldnames1 = ['time', 'uid', 'value', 'result']
                writer1 = csv.DictWriter(test1file, fieldnames = fieldnames1)
                writer1.writerow({fieldnames1[0]: str(datetime.datetime.now()) ,fieldnames1[1]: uid, fieldnames1[2]: value1, fieldnames1[3]: result})
        elif test == 2:
            with open('Test2.csv', 'a', newline='') as test2file:
                fieldnames2 = ['time', 'uid', 'value1', 'value2', 'value3', 'result']
                writer2 = csv.DictWriter(test2file, fieldnames = fieldnames2)
                writer2.writerow({fieldnames2[0]: str(datetime.datetime.now()) ,fieldnames2[1]: uid, fieldnames2[2]: value1, fieldnames2[3]: value2, fieldnames2[4]: value3, fieldnames2[5]: result})

root = tk.Tk()
app = Application(master=root)
app.master.title("UV Patch Testing Application")
app.master.maxsize(1000, 4000)
#app.master.iconbitmap('limelab.ico')
app.mainloop()
