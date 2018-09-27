import tkinter
import serial
import csv
import threading
import queue
import datetime
import serial.tools.list_ports
import sys
import visa
import os
import time
from ftplib import FTP

__author__ = "Justin Fu"
__copyright__ = "Copyright 2018, Helios Testing Script"
__version__ = "0.4.0"
__email__ = "justin.fu@pchintl.com"


class Application(tkinter.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.create_widgets()

        master.protocol("WM_DELETE_WINDOW", self.close)

        # Create a queue for serial to calculate
        self.serial_queue = queue.Queue()
        # Create a queue for sending DMM value
        self.DMM_queue = queue.Queue(maxsize=1)
        # Create an event for stopping the thread
        self.shutdown_event = threading.Event()
        # Create a queue for sending station number
        self.station_queue = queue.Queue(maxsize=1)
        
        self.serial_thread = SerialThread(self.serial_queue, self.DMM_queue, self.station_queue, self.shutdown_event)
        self.serial_thread.start()
        
        self.station_select()

    def create_widgets(self):

        # Frame1: Display UID
        self.uid_frame = tkinter.Frame(self, relief="raised", borderwidth=1)
        self.uid_frame.pack(fill='x')
        # UID label 
        self.uid_label = tkinter.Label(self.uid_frame, text="UID: ", font=("Counrier", 25))
        self.uid_label.pack(side="left", padx=10, pady=10)
        # UID box
        self.uid_box = tkinter.Entry(self.uid_frame, font=("Counrier", 25), bg="light gray")
        self.uid_box.pack(fill="both", padx=10, pady=10, expand=True)
 

        # Frame2: Test for ADC average
        self.test_avg_frame = tkinter.Frame(self, relief="raised", borderwidth=1)
        for i in range(5):
            self.test_avg_frame.columnconfigure(i, pad=10, weight=1, uniform="five")
        self.test_avg_frame.rowconfigure(0, pad=0)
        self.test_avg_frame.rowconfigure(1, pad=10)
        self.test_avg_frame.pack(fill='x')

        self.avg_label = tkinter.Label(self.test_avg_frame, text="AVG VOLT(mV)", font=("Counrier, 10"))
        self.avg_label.grid(row=0, column=3)
        # ADC average box
        self.avg_box = tkinter.Text(self.test_avg_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.avg_box.grid(row=1, column=3)
        # Test result
        self.result_avg_frame = tkinter.Frame(self.test_avg_frame, relief="raised", borderwidth=1)
        self.result_avg_frame.grid(row=0, column=4, rowspan=2, sticky='w'+'e'+'n'+'s')
        self.result_avg_label = tkinter.Label(self.result_avg_frame, font=("Counrier", 25))
        self.result_avg_label.pack(fill="none", expand=True)

        # Frame3: Test for charging/discharging
        self.test_cd_frame = tkinter.Frame(self, relief="raised", borderwidth=1)
        for i in range(5):
            self.test_cd_frame.columnconfigure(i, pad=10, weight=1, uniform="five")
        self.test_cd_frame.rowconfigure(0, pad=0)
        self.test_cd_frame.rowconfigure(1, pad=10)
        self.test_cd_frame.pack(fill='x')
        
        self.dmm_label = tkinter.Label(self.test_cd_frame, text="DMM VOLT(mV)", font=("Counrier, 10"))
        self.dmm_label.grid(row=0, column=0)
        self.charge_label = tkinter.Label(self.test_cd_frame, text="CHG VOLT(mV)", font=("Counrier, 10"))
        self.charge_label.grid(row=0, column=2)
        self.discharge_label = tkinter.Label(self.test_cd_frame, text="DISCHG VOLT(mV)", font=("Counrier, 10"))
        self.discharge_label.grid(row=0, column=3)
        # DMM box
        self.dmm_box = tkinter.Text(self.test_cd_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.dmm_box.grid(row=1, column=0)
        # Set button
        self.set_button = tkinter.Button(self.test_cd_frame, height=1, width=6, text="Get", font=("Counrier, 18"), command=self.dmm_set)
        self.set_button.grid(row=0, column=1, rowspan=2)
        # Charge box
        self.charge_box = tkinter.Text(self.test_cd_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.charge_box.grid(row=1, column=2)
        # Discharge box
        self.discharge_box = tkinter.Text(self.test_cd_frame, height=1, width=6, font=("Counrier, 25"), bg="light gray")
        self.discharge_box.grid(row=1, column=3)
        # Test result
        self.result_cd_frame = tkinter.Frame(self.test_cd_frame, relief="raised", borderwidth=1)
        self.result_cd_frame.grid(row=0, column=4, rowspan=2, sticky='w'+'e'+'n'+'s')
        self.result_cd_label = tkinter.Label(self.result_cd_frame, font=("Counrier", 25))
        self.result_cd_label.pack(fill="none", expand=True)

        # Station radiobutton
        station_show, product_line = self.station_setup()
        self.station_number = tkinter.IntVar()
        if station_show == '1':
            self.station_checkbox = tkinter.Radiobutton(self, text="Station_1", variable=self.station_number, value=1, command=self.station_select)
            self.station_checkbox.pack(side="left", padx=10)
        elif station_show == '2':
            self.station_checkbox = tkinter.Radiobutton(self, text="Station_2", variable=self.station_number, value=2, command=self.station_select)
            self.station_checkbox.pack(side="left", padx=10)
        elif station_show == '3':
            self.station_checkbox = tkinter.Radiobutton(self, text="Station_3", variable=self.station_number, value=3, command=self.station_select)
            self.station_checkbox.pack(side="left", padx=10)
        elif station_show == '4':
            self.station_checkbox = tkinter.Radiobutton(self, text="Station_4", variable=self.station_number, value=4, command=self.station_select)
            self.station_checkbox.pack(side="left", padx=10)
        else:
            print("Station setup error.")
            time.sleep(1)
            sys.exit()
        
        self.station_checkbox.select()

        self.line_label = tkinter.Label(self, text="Product Line: "+product_line)
        self.line_label.pack(side="left", padx=10)
        self.version_label = tkinter.Label(self, text="Version: "+__version__)
        self.version_label.pack(side="right", padx=10)

        self.origin_color = self.result_avg_frame.cget("background")

    def station_select(self):
        selection = self.station_number.get()
        print(selection)
        if selection == 1:
            self.station_queue.put(1)
        elif selection == 2:
            self.station_queue.put(2)
        elif selection == 3:
            self.station_queue.put(3)
        elif selection == 4:
            self.station_queue.put(4)
        
        if self.DMM_queue.full():
            self.DMM_queue.get()
            print("clear queue")
            self.dmm_box.delete(0.0, "end")
    
    def dmm_set(self):
        if self.station_number.get() == 2:
            rm = visa.ResourceManager()
            for inst in rm.list_resources():
                try:
                    rigol = rm.open_resource(inst)
                    break
                except:
                    rigol = ""
            if not rigol:
                print("no rigol")
                dmm_voltage = -1
                self.dmm_box.delete(0.0, "end")
                self.dmm_box.insert(0.0, "nodmm")
            else:
                print(rigol.query("*IDN?"))
                dmm_voltage = round(float(rigol.query(":measure:voltage:dc?"))*1000, 2)
                self.dmm_box.delete(0.0, "end")
                self.dmm_box.insert(0.0, dmm_voltage)

            if self.DMM_queue.full():
                self.DMM_queue.get()
                print("clear queue")
            self.DMM_queue.put(dmm_voltage)
            print(dmm_voltage)


    def dmm_set_old(self):
        dmm_value = self.dmm_box.get("1.0", "end")
        dmm_value = dmm_value.split()
        
        if len(dmm_value):
            dmm_value = dmm_value[0]
        else:
            dmm_value = "no value"
        
        if self.is_int_or_float(dmm_value):
            dmm_voltage = float(dmm_value)
        else:
            dmm_voltage = -1
        
        if self.DMM_queue.full():
            self.DMM_queue.get()
            print("clear queue")
        self.DMM_queue.put(dmm_voltage)
        print(dmm_voltage)

    
    def is_int_or_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    
        

    def close(self):
        self.shutdown_event.set()
        self.serial_thread.join()
        root.destroy()

    def GUI_update(self):
        if not self.serial_queue.empty():
            message = self.serial_queue.get()
            if message["UID"] == None:
                self.uid_box.delete(0, "end")
            else:
                self.uid_box.delete(0, "end")
                self.uid_box.insert(0, message["UID"])

            if message["VOLT1"] == None:
                self.avg_box.delete(0.0, "end")
            else:
                self.avg_box.insert(0.0, message["VOLT1"])

            if message["DMM"] == None:
                self.dmm_box.delete(0.0, "end")
            else:
                self.dmm_box.insert(0.0, message["DMM"])

            if message["VOLT2"] == None:
                self.charge_box.delete(0.0, "end")
            else:
                self.charge_box.insert(0.0, message["VOLT2"])

            if message["VOLT3"] == None:
                self.discharge_box.delete(0.0, "end")
            else:
                self.discharge_box.insert(0.0, message["VOLT3"])

            if message["RES1"] == None:
                self.result_avg_frame.configure(background=self.origin_color)
                self.result_avg_label.configure(text='', background=self.origin_color)
            elif message["RES1"]%10:
                self.result_avg_frame.configure(background="red")
                self.result_avg_label.configure(text=message["RES1"], background="red")
            elif message["RES1"]%10 == 0:
                self.result_avg_frame.configure(background="green")
                self.result_avg_label.configure(text="PASS", background="green")

            if message["RES2"] == None:
                self.result_cd_frame.configure(background=self.origin_color)
                self.result_cd_label.configure(text='', background=self.origin_color)
            elif message["RES2"]==99:
                self.result_cd_frame.configure(background="yellow")
                self.result_cd_label.configure(text="REDO", background="yellow")
            elif message["RES2"]%10:
                self.result_cd_frame.configure(background="red")
                self.result_cd_label.configure(text=message["RES2"], background="red")
            elif message["RES2"]%10 == 0:
                self.result_cd_frame.configure(background="green")
                self.result_cd_label.configure(text="PASS", background="green")


        root.after(200, self.GUI_update) 

    def station_setup(self):
        try:
            setup_file = open("station_setup", 'r')
        except FileNotFoundError:
            print("No setup file")
            return "error", 'D'
        file_content = setup_file.readlines()
        first_line = file_content[0].split()
        if not first_line:
            print("Empty")
            return "error"
        station = first_line[0]
        print("Test:",station)

        try:
            second_line = file_content[1].split()
        except IndexError:
            second_line = '0'
        if second_line[0] == '0':
            product_line = '0'
        elif second_line[0] == '1':
            product_line = '1'
        elif second_line[0] == '2':
            product_line = '2'
        elif second_line[0] == '3':
            product_line = '3'
        else:
            product_line = 'D'
        print("Line:", product_line)
        return station, product_line


class SerialThread(threading.Thread):

    def __init__(self, send_queue, receive_queue, station_queue, event):
        threading.Thread.__init__(self)
        # Create an event for stopping the thread
        self.shutdown_flag = event
        # Create a queue for sending UID and ADC value
        self.send_queue = send_queue
        # Create a queue for receiving DMM value
        self.receive_queue = receive_queue
        # Create a queue for setting station
        self.station_queue = station_queue
        # List all serial ports
        ports = list(serial.tools.list_ports.comports())
        # Exit when no serial port exist
        if not ports:
            sys.exit()
        # Check and find out the serial port for MSP430
        for p in ports:
            if "MSP430" in str(p):
                port_name = p.device
                break
            else:
                port_name = ""
        if not port_name:
            sys.exit()
        # Setup serial port
        self.ser = serial.Serial(port_name, 9600, timeout=0.1)


    def run(self):

        sensor_out_count = 0
        sensor_out_max = 5
        head = ""
        body_count = 0
        body_max= 30
        tail = "END"

        test = 1
        
        message = {"UID": None, "VOLT1": None, "RES1": None, "DMM": None, "VOLT2": None, "VOLT3": None, "RES2": None}
        
        self.create_directory()
        self.line = self.line_setup()

        while True:
            
            # Check the shutdown event
            if self.shutdown_flag.is_set():
                return
            
            if self.station_queue.full():
                print("get message from station queue")
                test = self.station_queue.get()

            # Read a line from serial port
            read_out = self.ser.readline().decode("latin1")
            # The processing will reset when the sensor is out for a while
            if not read_out and sensor_out_count < sensor_out_max and head:
                sensor_out_count += 1
            elif not read_out and sensor_out_count == sensor_out_max and head:
                head = ""
                sensor_out_count = 0
                message = {"UID": None, "VOLT1": None, "RES1": None, "DMM": None, "VOLT2": None, "VOLT3": None, "RES2": None}
                print(message)
                self.send_queue.put(message)
                # clear the dmm_queue
                if self.receive_queue.full():
                    self.receive_queue.get()
           
            # Acquire the first UID and the following ADC data
            if "UID:" in read_out and not head:
                head = read_out[read_out.find('[')+1: read_out.find(']')]
                
                # Reset body message counting 
                body_count = 0
                
                message["UID"] = head
                self.send_queue.put(message)
                #print(message)

            elif "Block 04 Data:" in read_out and head and body_count < body_max:
                
                position = read_out.find('[') + 5
                body = read_out[position+2: position+4] + read_out[position: position+2]
                print(body)
                try:
                    voltage = round((int(body, 16))*0.9/16383/2*1000, 2)
                except ValueError:
                    sensor_out_count = 0
                    continue
                # Necessary to reset the sensor_out_cout because there is an empty reading after each cycle
                sensor_out_count = 0
                
                if test == 1 or test == 3:
                    if body_count == 0:
                        # When body_count is zero, it means the UID is detect
                        # Clean the previous data
                        voltage_sum = 0
                        voltage_avg = 0
                    elif body_count >= 10 and body_count <20:
                        # Do nothing for the first 10 sets of data
                        # Sum up the following 10 sets of data
                        voltage_sum += voltage
                    elif body_count == 21:
                        # Set the body_count to max, when it reach to the 21st set of ADC value which will stop recording the block 04 data
                        # Count the average value
                        body_count = body_max
                        voltage_avg = voltage_sum/10
                        # Do the judgement
                        if voltage_avg > 5:
                            res = test * 10 + 1
                        else:
                            res = test * 10
                        # write the result to the message
                        message["VOLT1"] = voltage_avg
                        message["RES1"] = res
                        print(message)
                        # write the result to the log file
                        self.record_result(test, message)
                        # send the message to queue
                        self.send_queue.put(message)

                elif test == 2 or test == 4:
                    if body_count == 0:
                        # When body_count is zero, it means the UID is detect
                        # At the same time, it will come with the first set of ADC value
                        # the first set of ADC value is the charged value
                        voltage2 = voltage
                    elif body_count == 1:
                        # Set the body_count to max, when it reach to the 2nd set of ADC value which will stop recording the block 04 data
                        # the second set of ADC value is the discharged value
                        body_count = body_max
                        voltage3 = voltage
                        # write the result to the message
                        message["VOLT2"] = voltage2
                        message["VOLT3"] = voltage3
                        # if it is the second station, check if any DMM input value exist
                        if self.receive_queue.empty() and test == 2:
                            message["RES2"] = 99
                            print("empty queue")
                        elif test == 2:
                            dmm_voltage = self.receive_queue.get()
                            message["DMM"] = dmm_voltage
                            # check if the DMM input value is invalid
                            if dmm_voltage == -1:
                                message["DMM"] = None
                                message["RES2"] = 99
                                print("empty box")
                            elif abs(voltage2-18) > 5:
                                message["RES2"] = 21
                            elif voltage3 > 5:
                                message["RES2"] = 22
                            elif abs(dmm_voltage-18) > 5:
                                message["RES2"] = 23
                            elif abs(voltage2-dmm_voltage) > 3.5:
                                message["RES2"] = 24
                            else:
                                message["RES2"] = 20
                        elif test == 4:
                            if abs(voltage2-15) > 5:
                                message["RES2"] = 41
                            elif voltage3 > 5:
                                message["RES2"] = 42
                            else:
                                message["RES2"] = 40
                        
                        print(message)

                        # write the result to the log file
                        self.record_result(test, message)
                        # send the message to queue
                        self.send_queue.put(message)
                        
                    



                body_count += 1

            elif "Block 04 Data:" in read_out and head and body_count >= body_max:
                sensor_out_count = 0

    def create_directory(self):
        dirname = "C:\PCH\HeliosLog"
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def record_result(self, test, message):
        if test == 1 or test == 3:
            file_name = "C:\PCH\HeliosLog\Test"+str(test)+"_Line"+self.line+'_'+str(datetime.date.today())+".csv"
            with open(file_name, 'a', newline='') as testfile:
                fieldnames = ["time", "uid", "volt1", "result"]
                writer = csv.DictWriter(testfile, fieldnames=fieldnames)
                writer.writerow({
                    fieldnames[0]: str(datetime.datetime.now()), 
                    fieldnames[1]: message["UID"], 
                    fieldnames[2]: message["VOLT1"],
                    fieldnames[3]: message["RES1"]})
            
            self.ftp_update(file_name)

        elif test == 2 or test == 4:
            file_name = "C:\PCH\HeliosLog\Test"+str(test)+"_Line"+self.line+'_'+str(datetime.date.today())+".csv"
            with open(file_name, 'a', newline='') as testfile:
                fieldnames = ["time", "uid", "dmm", "volt2", "volt3", "result"]
                writer = csv.DictWriter(testfile, fieldnames=fieldnames)
                writer.writerow({
                    fieldnames[0]: str(datetime.datetime.now()),
                    fieldnames[1]: message["UID"],
                    fieldnames[2]: message["DMM"],
                    fieldnames[3]: message["VOLT2"],
                    fieldnames[4]: message["VOLT3"],
                    fieldnames[5]: message["RES2"]})

            self.ftp_update(file_name)


    def ftp_update(self, file_name):
        try:
            ftp = FTP("pchintl.net")
        except:
            print("FTP connection error")
            pass

        ftp.login("L'Oreal Helios", "PCH#2018")

        file_path = os.path.basename(file_name)[0:5]
        try:
            ftp.cwd("HeliosLog/"+file_path)
        except:
            ftp.mkd("HeliosLog/"+file_path)
            ftp.cwd("HeliosLog/"+file_path)

        with open(file_name, 'rb') as fobj:
            ftp.storlines("STOR " + os.path.basename(file_name), fobj)

        ftp.quit()
    
    def line_setup(self):
        try:
            setup_file = open("station_setup", 'r')
        except FileNotFoundError:
            print("No setup file")
            return 'D'
        file_content = setup_file.readlines()
        try:
            second_line = file_content[1].split()
        except IndexError:
            second_line = '0'
        if second_line[0] == '0':
            product_line = '0'
        elif second_line[0] == '1':
            product_line = '1'
        elif second_line[0] == '2':
            product_line = '2'
        elif second_line[0] == '3':
            product_line = '3'
        else:
            product_line = 'D'
        print("Line:", product_line)
        return product_line


root = tkinter.Tk()
app = Application(master=root)
app.master.title("Helio Testing Script")
app.master.maxsize(1000,4000)
app.GUI_update()
app.mainloop()
