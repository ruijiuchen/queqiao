import os
import tkinter as tk
from tkinter import filedialog
import subprocess
import time
import threading
import paramiko
import sys
def is_file_written(directory,file, timeout=10):
    """
    Check if a file has been written and its size remains constant for a certain period.    
    Args:
        file_path (str): The path to the file.
        timeout (int): The maximum time to wait (in seconds) for the file to stabilize.
    Returns:
        bool: True if the file has been written and its size remains constant; False otherwise.
    """
    file_path = directory + "/" + file
    if not os.path.exists(file_path):
        return False
    
    initial_size = os.path.getsize(file_path)
    time_elapsed = 0
    
    while time_elapsed < timeout:
        time.sleep(5)  # Wait for 1 second
        current_size = os.path.getsize(file_path)
        print("checking ",file," t = ",time_elapsed, " s, current_size: ", current_size/1024/1024," MB")
        if current_size == initial_size:
            return True
        
        initial_size = current_size
        time_elapsed += 5
    return False

def list_files_in_directory(directory, end=".iq.tdms"):
    #print("chenrj list_files_in_directory 1 ")
    try:
        files0 = os.listdir(directory)
        files0.sort()  # Sort the list in place alphabetically
    except FileNotFoundError:
        # If the directory doesn't exist, return an empty list
        files0 = []
    #print("chenrj list_files_in_directory 2 ")
    files=[]
    #print("list_files_in_directory ",len(files0))
    for i in range(0, len(files0)):
        #print("chenrj list_files_in_directory 2-1 ")
        if i <len(files0) - 2:
            if files0[i].endswith(end):  # Check if the file has the .tdms extension
                files.append(files0[i])
        else:
            #if they are the last two files
            #print("chenrj list_files_in_directory 4 files0[i] ",files0[i])
            #print("files0",files0)
            if is_file_written(directory,files0[i],15) and files0[i].endswith(end): # bug here.
                files.append(files0[i])
    #print("chenrj list_files_in_directory 3 ")
    sorted_files = sorted(files)  # Sort files by name
    #print("chenrj list_files_in_directory 4 sorted_files=",sorted_files)
    return sorted_files
    #return files
    
def browse_folder_and_update_list_filebox(folder_entry_ntcap, folder_entry_luster, default_path_ntcap, default_path_luster, file_listbox, ssh, file_listbox_luster, analyzed_files_name="synced_files_iq.txt",end=".iq.tdms"):
    #print("chenrj ...0")
    selected_directory = filedialog.askdirectory(initialdir=default_path_ntcap)
    #print("chenrj ... browse_folder_and_update_list_filebox selected_directory=",selected_directory )
    if selected_directory:
        directory_name   = os.path.basename(selected_directory)
        parent_directory = os.path.dirname(default_path_luster)
        selected_directory_luster = parent_directory + "/" + directory_name 
        folder_entry_ntcap.delete(0, tk.END)  # Clear previous entry
        folder_entry_ntcap.insert(0, selected_directory)
    
        folder_entry_luster.delete(0, tk.END)  # Clear previous entry
        folder_entry_luster.insert(0, selected_directory_luster)
        default_path_luster = selected_directory_luster
        
        file_listbox.delete(0, tk.END)
        update_file_list(file_listbox, selected_directory, analyzed_files_name, end)
        update_file_list_ssh(file_listbox_luster, ssh, default_path_luster,"","")
        
def get_synced_files(synced_files_file = "synced_files_iq.txt"):
    # Path to the text file to keep track of synchronized files
    if os.path.exists(synced_files_file):
        with open(synced_files_file, "r") as file:
            #synced_files = file.read().splitlines()
            synced_files = [line.split()[0] for line in file.read().splitlines()]
            return synced_files
    else:
        return []

def add_synced_file(synced_files_file, directory, file_name, elapsed_time):
    with open(synced_files_file, "a") as file:
        file.write(directory + "/" + file_name + " " + str(elapsed_time)+ " [second]\n")
    
    name = os.path.basename(directory)
    #print("chenrj name = ",name )
    new_synced_files_file = name + "_" + synced_files_file
    with open(new_synced_files_file, "a") as file:
        file.write(directory + "/" + file_name + " " + str(elapsed_time)+ " [second]\n")
    return new_synced_files_file

def create_directory_on_server(folder_entry_ntcap_iq, folder_entry_luster_iq,folder_entry_ntcap_sc, folder_entry_luster_sc):
    path_ntcap_iq = folder_entry_ntcap_iq.get()
    path_luster_iq = folder_entry_luster_iq.get()
    path_ntcap_sc = folder_entry_ntcap_sc.get()
    path_luster_sc = folder_entry_luster_sc.get()

    BaseDir_path_ntcap_iq = os.path.basename(path_ntcap_iq)
    BaseDir_path_luster_iq = os.path.basename(path_luster_iq)
    BaseDir_path_ntcap_sc = os.path.basename(path_ntcap_sc)
    BaseDir_path_luster_sc = os.path.basename(path_luster_sc)
    
    if BaseDir_path_ntcap_iq != BaseDir_path_luster_iq:
        error_message = f"Error: Local directory '{BaseDir_path_ntcap_iq}' and server directory '{BaseDir_path_luster_iq}' do not match."
        print(error_message)
        folder_entry_ntcap_iq.config(bg="red")
        folder_entry_luster_iq.config(bg="red")
        return path_luster_iq, path_luster_sc,False
    else:
        folder_entry_ntcap_iq.config(bg="white")
        folder_entry_luster_iq.config(bg="white")
        
    if BaseDir_path_ntcap_sc!=BaseDir_path_luster_sc:
        error_message = f"Error: Local directory '{BaseDir_path_ntcap_sc}' and server directory '{BaseDir_path_luster_sc}' do not match."
        print(error_message)
        folder_entry_ntcap_sc.config(bg="red")
        folder_entry_luster_sc.config(bg="red")
        return path_luster_iq, path_luster_sc,False
    else:
        folder_entry_ntcap_sc.config(bg="white")
        folder_entry_luster_sc.config(bg="white")
    
    directory_iq = os.path.basename(path_ntcap_iq)
    directory_sc = os.path.basename(path_ntcap_sc)
    
    print(f"check the foler {path_luster_iq} whether exist." )
    parts = path_luster_iq.split(":")
    if len(parts) > 1:
        username_host = parts[0]
        remote_directory_iq=parts[1]
        username, host = username_host.split("@")
        print("Username:", username)
        print("Host:", host)
        print("Remote directory(iq):", remote_directory_iq)
    else:
        print("Invalid remote path format.")
    
    parts = path_luster_sc.split(":")
    if len(parts) > 1:
        username_host = parts[0]
        remote_directory_sc=parts[1]
        username, host = username_host.split("@")
        print("Username:", username)
        print("Host:", host)
        print("Remote directory(sc):", remote_directory_sc)
    else:
        print("Invalid remote path format.")
    
    # Create an SSH client object
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Connect to the remote server
    ssh_client.connect(host,22,username)
    
    # Execute the SSH command to create the directory
    ssh_command_iq = f'mkdir -p {remote_directory_iq}'
    stdin_iq, stdout_iq, stderr_iq = ssh_client.exec_command(ssh_command_iq)
    ssh_command_sc = f'mkdir -p {remote_directory_sc}'
    stdin_sc, stdout_sc, stderr_sc = ssh_client.exec_command(ssh_command_sc)
    
    # Get the command execution results
    print('stdout (iq):', stdout_iq.read().decode())
    print('stderr (iq):', stderr_iq.read().decode())
    # Get the command execution results
    print('stdout (sc):', stdout_sc.read().decode())
    print('stderr (sc):', stderr_sc.read().decode())
    
    # Close the SSH connection
    ssh_client.close()

    return path_luster_iq, path_luster_sc,True
    
def set_listbox_iterm_color(file_listbox, file, color="green"):
    # Update the listbox item color
    file_list_items = file_listbox.get(0, tk.END)  # Get all items in the listbox
    if file in file_list_items:
        index = file_listbox.get(0, tk.END).index(file)
        file_listbox.itemconfig(index, {'bg': color})

def sync_files_worker_iq(default_path_ntcap_iq,default_path_luster_iq, file_listbox_iq,file_listbox_sc,start_button,should_stop_sync,elapsed_times_iq, hostname, username, keyfilename, ssh, file_listbox_luster_iq,synced_files_iq,synced_files_iq_end):
    while not should_stop_sync[0]:
        time.sleep(5)
        print("should_stop_sync[0] = ",should_stop_sync[0])
        if default_path_ntcap_iq:
        
            update_file_list(file_listbox_iq,default_path_ntcap_iq,synced_files_iq,synced_files_iq_end)# Update the file list with the new directory
            
            synced_files = get_synced_files(synced_files_iq)        
            files = list_files_in_directory(default_path_ntcap_iq,synced_files_iq_end)
            for file in files:
                if should_stop_sync[0]:  # Check if user wants to stop syncing
                    break
                file_fullpath=default_path_ntcap_iq + "/" +file
                if file_fullpath not in synced_files:
                    start_time = time.time()  # Record the start time
                    command = f"scp -v {default_path_ntcap_iq}/{file} {username}@{hostname}:{default_path_luster_iq} 2>&1 | tee -a transfer_log_iq.txt"
                    try:
                        # Update the listbox item color
                        set_listbox_iterm_color(file_listbox_iq, file, "yellow")
                        subprocess.run(command, shell=True, check=True)
                        end_time = time.time()  # Record the end time
                        elapsed_time = end_time - start_time
                        file_path = os.path.join(default_path_ntcap_iq, file)
                        file_size = os.path.getsize(file_path) / (1024)  # Convert bytes to megabytes
                        speed=file_size/elapsed_time
                        synced_files_file = synced_files_iq
                        new_synced_files_file = add_synced_file(synced_files_file,default_path_ntcap_iq, file, elapsed_time)
                        command = f"rsync -avz  {new_synced_files_file} {username}@{hostname}:{default_path_luster_iq}/{synced_files_file}"
                        #print("chenrj command = ", command)
                        #command = f"rsync -avz  synced_files_iq.txt ../analyze_iq_sc"
                        subprocess.run(command, shell=True, check=True)
                        
                        # Update the listbox item color
                        set_listbox_iterm_color(file_listbox_iq, file, "green")
                        # Get the current file's index in the list
                        current_file_name=file
                        current_file_index = files.index(current_file_name) if current_file_name in files else None
                        if current_file_index is not None:
                            scroll_position = max(0, (current_file_index - 2) / len(files))  # You might want to adjust the offset
                            file_listbox_iq.yview_moveto(scroll_position)
                        #update_file_list_ssh(file_listbox_luster_iq, ssh, default_path_luster_iq,"","")
                        #update_file_list(file_listbox_iq,default_path_ntcap_iq,synced_files_iq,synced_files_iq_end)# Update the file list with the new directory
                        
                    except subprocess.CalledProcessError:
                        print(f"File synchronization failed for: {file}")
                        # Update the listbox item color
                        set_listbox_iterm_color(file_listbox_iq, file, "red")

def sync_files_worker_sc(default_path_ntcap_sc, default_path_luster_sc ,file_listbox_iq, file_listbox_sc,start_button,should_stop_sync, hostname, username, keyfilename, ssh, file_listbox_luster_sc, synced_files_sc,synced_files_sc_end):
    while not should_stop_sync[0]:
        time.sleep(5)
        ################ sc #################################################
        if default_path_ntcap_sc:
            update_file_list(file_listbox_sc,default_path_ntcap_sc,synced_files_sc,synced_files_sc_end)# Update the file list with the new directory
            synced_files = get_synced_files(synced_files_sc)        
            files = list_files_in_directory(default_path_ntcap_sc,synced_files_sc_end)
            for file in files:
                if should_stop_sync[0]:  # Check if user wants to stop syncing
                    break
                file_fullpath=default_path_ntcap_sc + "/" + file
                if file_fullpath not in synced_files:
                    start_time = time.time()  # Record the start time
                    command = f"scp -v  {default_path_ntcap_sc}/{file} {username}@{hostname}:{default_path_luster_sc} 2>&1 | tee -a transfer_log_sc.txt"
                    try:
                        set_listbox_iterm_color(file_listbox_sc, file, "yellow")
                        
                        subprocess.run(command, shell=True, check=True)
                        end_time = time.time()  # Record the end time
                        elapsed_time = end_time - start_time
                        file_path = os.path.join(default_path_ntcap_sc, file)
                        file_size = os.path.getsize(file_path) / (1024)  # Convert bytes to megabytes
                        speed=file_size/elapsed_time
                        synced_files_file = synced_files_sc
                        new_synced_files_file = add_synced_file(synced_files_file,default_path_ntcap_sc, file, elapsed_time)
                        command = f"rsync -avz  {new_synced_files_file} {username}@{hostname}:{default_path_luster_sc}/{synced_files_file}"
                        subprocess.run(command, shell=True, check=True)
                        
                        # Update the listbox item color
                        set_listbox_iterm_color(file_listbox_sc, file, "green")
                        # Get the current file's index in the list
                        current_file_name=file
                        current_file_index = files.index(current_file_name) if current_file_name in files else None
                        if current_file_index is not None:
                            scroll_position = max(0, (current_file_index - 2) / len(files))  # You might want to adjust the offset
                            file_listbox_sc.yview_moveto(scroll_position)
                        #update_file_list_ssh(file_listbox_luster_sc, ssh, default_path_luster_sc,"","")
                        #update_file_list(file_listbox_sc,default_path_ntcap_sc,synced_files_sc,synced_files_sc_end)# Update the file list with the new directory
                        
                    except subprocess.CalledProcessError:
                        print(f"File synchronization failed for: {file}")
                        # Update the listbox item color
                        set_listbox_iterm_color(file_listbox_sc, file, "red")
        
def sync_files_to_server(start_button,stop_button, folder_entry_ntcap_iq, folder_entry_luster_iq,folder_entry_ntcap_sc, folder_entry_luster_sc,default_path_ntcap_iq,default_path_luster_iq,file_listbox_iq,file_listbox_sc,reset_button,browse_button_ntcap_iq,browse_button_ntcap_sc,should_stop_sync, folder_entry_hostname, folder_entry_username, folder_entry_keyfilename,ssh,file_listbox_luster_iq,file_listbox_luster_sc,synced_files_iq,synced_files_iq_end,synced_files_sc,synced_files_sc_end):
    should_stop_sync[0] = False
    hostname               = folder_entry_hostname.get()
    username               = folder_entry_username.get()
    keyfilename            = folder_entry_keyfilename.get()
    default_path_ntcap_iq  = folder_entry_ntcap_iq.get()
    default_path_luster_iq = folder_entry_luster_iq.get()
    default_path_ntcap_sc  = folder_entry_ntcap_sc.get()
    default_path_luster_sc = folder_entry_luster_sc.get()
    files_luster_iq = create_remote_directory(default_path_luster_iq, ssh)
    files_luster_sc = create_remote_directory(default_path_luster_sc, ssh)
    update_file_list_ssh(file_listbox_luster_iq, ssh, default_path_luster_iq,"","")
    update_file_list_ssh(file_listbox_luster_sc, ssh, default_path_luster_sc,"","")
    start_button.config(state=tk.DISABLED)  # Disable the start button during syncing

    stop_button.config(state=tk.NORMAL) # Enable the stop button later when needed
    folder_entry_hostname.config(state="disabled")
    folder_entry_username.config(state="disabled")
    folder_entry_keyfilename.config(state="disabled")
    folder_entry_ntcap_iq.config(state="disabled")  # Disable user input
    folder_entry_luster_iq.config(state="disabled")  # Disable user input
    folder_entry_ntcap_sc.config(state="disabled")  # Disable user input
    folder_entry_luster_sc.config(state="disabled")  # Disable user input
    reset_button.config(state="disabled")  # Disable the reset button
    browse_button_ntcap_iq.config(state="disabled")
    browse_button_ntcap_sc.config(state="disabled")

    # Initialize an empty dictionary to store the elapsed_time for each file
    elapsed_times_iq = {}
    
    sync_thread_iq = threading.Thread(target=lambda:sync_files_worker_iq(default_path_ntcap_iq,default_path_luster_iq,file_listbox_iq,file_listbox_sc,start_button,should_stop_sync,elapsed_times_iq, hostname, username, keyfilename, ssh, file_listbox_luster_iq,synced_files_iq,synced_files_iq_end))
    sync_thread_iq.start()

    sync_thread_sc = threading.Thread(target=lambda:sync_files_worker_sc(default_path_ntcap_sc, default_path_luster_sc,file_listbox_iq,file_listbox_sc,start_button,should_stop_sync, hostname, username, keyfilename, ssh, file_listbox_luster_sc,synced_files_sc,synced_files_sc_end))
    sync_thread_sc.start()
    #
    
def ini_file_listbox(file_listbox_iq):
    existing_items = file_listbox_iq.get(0, tk.END)
    for file in existing_items:
        index = file_listbox_iq.get(0, tk.END).index(file)
        file_listbox_iq.itemconfig(index, {'bg': 'white'})
        file_listbox_iq.yview_moveto(0)
        
def reset_sync(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc):
    try:
        os.remove("synced_files_iq.txt")
        print("synced_files_iq.txt has been deleted.")
    except FileNotFoundError:
        print("synced_files_iq.txt not found. No action taken.")
    ini_file_listbox(file_listbox_iq)
    try:
        os.remove("synced_files_sc.txt")
        print("synced_files_sc.txt has been deleted.")
    except FileNotFoundError:
        print("synced_files_sc.txt not found. No action taken.")
    ini_file_listbox(file_listbox_sc)
    
def reset_sim_worker_iq(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc):
    command = f"bash /data.local1/simulated_data/auto_copy_iq.sh"
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"bash /data.local1/simulated_data/auto_copy_iq.sh")
        
def reset_sim_worker_sc(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc):
    command = f"bash /data.local1/simulated_data/auto_copy_sc.sh"
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"bash /data.local1/simulated_data/auto_copy_sc.sh")
        
def reset_sim(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc):
    
    reset_sim_thread_iq = threading.Thread(target=lambda:reset_sim_worker_iq(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc))
    reset_sim_thread_iq.start()
    
    reset_sim_thread_sc = threading.Thread(target=lambda:reset_sim_worker_sc(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc))
    reset_sim_thread_sc.start()
        
def stop_sync_worker(stop_button,start_button,folder_entry_ntcap_iq,folder_entry_luster_iq,folder_entry_ntcap_sc,folder_entry_luster_sc,reset_button,browse_button_ntcap_iq,browse_button_ntcap_sc,should_stop_sync,file_listbox_iq,file_listbox_sc, folder_entry_hostname, folder_entry_username, folder_entry_keyfilename):
    while should_stop_sync[0]: # keep the threading runing until should_stop_analyze[0] = True.
        yellow_files_iq = []  # # Used to store file names with yellow color
        for item_index in range(file_listbox_iq.size()):
            item_color = file_listbox_iq.itemcget(item_index, 'bg')
            item_name = file_listbox_iq.get(item_index)
            if item_color == 'yellow':
                yellow_files_iq.append(item_name)
                
        yellow_files_sc = []  # # Used to store file names with yellow color
        for item_index in range(file_listbox_sc.size()):
            item_color = file_listbox_sc.itemcget(item_index, 'bg')
            item_name = file_listbox_sc.get(item_index)
            if item_color == 'yellow':
                yellow_files_sc.append(item_name)

        if len(yellow_files_iq) != 0 or len(yellow_files_sc) !=0:
            # Blink the stop_button by changing its background color
            stop_button.config(bg='yellow')
            time.sleep(0.5)
            stop_button.config(bg='green')
            time.sleep(0.5)
        else:
            # No yellow items, stop blinking
            time.sleep(1)
            
            #####2024.02.15 12:16 don't add this code!#####
            ########  should_stop_sync[0]=True
            ################################################
            #print("  chenrj ... stop_sync_worker")
            original_bg_color = start_button.cget('bg')
            stop_button.config(state=tk.DISABLED)  # Disable the stop button
            stop_button.config(bg=original_bg_color)  # Restore the original color
            start_button.config(state=tk.NORMAL)
            folder_entry_hostname.config(state="normal")
            folder_entry_username.config(state="normal")
            folder_entry_keyfilename.config(state="normal")
            folder_entry_ntcap_iq.config(state="normal")  # Enable user input
            folder_entry_luster_iq.config(state="normal")  # Enable user input
            folder_entry_ntcap_sc.config(state="normal")  # Enable user input
            folder_entry_luster_sc.config(state="normal")  # Enable user input
            reset_button.config(state="normal")  # Enable reset_button
            browse_button_ntcap_iq.config(state="normal")
            browse_button_ntcap_sc.config(state="normal")
            break
            
def stop_sync(stop_button,start_button,folder_entry_ntcap_iq,folder_entry_luster_iq,folder_entry_ntcap_sc,folder_entry_luster_sc,reset_button,browse_button_ntcap_iq,browse_button_ntcap_sc,should_stop_sync,file_listbox_iq,file_listbox_sc, folder_entry_hostname, folder_entry_username, folder_entry_keyfilename):
    should_stop_sync[0] =True
    
    stop_sync_worker_thread = threading.Thread(target=stop_sync_worker,args=(stop_button,start_button,folder_entry_ntcap_iq,folder_entry_luster_iq,folder_entry_ntcap_sc,folder_entry_luster_sc,reset_button,browse_button_ntcap_iq,browse_button_ntcap_sc,should_stop_sync,file_listbox_iq,file_listbox_sc, folder_entry_hostname, folder_entry_username, folder_entry_keyfilename))
    stop_sync_worker_thread.start()
    
def update_file_list(file_listbox,directory,synced_files_name="synced_files_iq.txt",end=".iq.tdms"):
    #print("update_file_list start!")

    files = list_files_in_directory(directory,end)
    #print("directory ",directory)
    #print("files ",files)
    file_listbox.delete(0, tk.END)
    scroll_position=0
    
    for file in files:
        file_listbox.insert(tk.END, file)
        
    synced_files = get_synced_files(synced_files_name)
    
    for file in files:
        file_fullpath=directory+"/"+file
        if file_fullpath in synced_files:
            set_listbox_iterm_color(file_listbox, file, "green")
    # Scroll to the last item
    file_listbox.yview(tk.END)
    #print("update_file_list completed!")
    
def update_file_list_ssh(file_listbox, ssh, directory, synced_files_name="synced_files_iq.txt", end=".iq.tdms"):
    #print("chenrj ... ",update_file_list_ssh)
    #print("chenrj ... directory ",directory)
    try:
        # Execute 'ls' command remotely to list files in the specified directory
        stdin, stdout, stderr = ssh.exec_command(f"ls {directory}")
        
        # Read the command output and split it into a list of filenames
        files = stdout.read().decode().split('\n')
        
        # Filter files by the specified end pattern
        files = [file for file in files if file.endswith(end)]
        #print("chenrj ... files ",files)
        # Update the file list in the file_listbox
        file_listbox.delete(0, tk.END)
        for file in files:
            file_listbox.insert(tk.END, file)
        # Scroll to the last item
        file_listbox.yview(tk.END)
        
    except Exception as e:
        # Handle any exceptions that may occur during the process
        print(f"Error updating file list: {e}")
    
######################################################################
import toml

def read_paths_config(file_path):
    with open(file_path, "r") as file:
        config = toml.load(file)
    #print("chenrj2 ",config)
    return config["paths"]

def list_directory_contents(ssh_client, remote_path):
    """
    List the contents of a remote directory using the 'ls' command.
    
    Parameters:
    - ssh_client (paramiko.SSHClient): An established SSH client for connecting to the remote server.
    - remote_path (str): The path of the remote directory to list.
    """
    try:
        # Execute 'ls' command to list directory contents
        
        stdin, stdout, stderr = ssh_client.exec_command(f"ls {remote_path}")
        
        # Read and print the command output
        output = stdout.read().decode().strip()
        #print(f"Contents of remote directory {remote_path}:\n{output}")
        return output
    
    except Exception as e:
        # Handle any exceptions that may occur during the process
        print(f"Error listing directory contents: {e}")
        return []
    
def create_remote_directory(remote_path, ssh_client):
    """
    Create a remote directory on the server using SSH.
    
    Parameters:
    - remote_path (str): The path of the remote directory to be checked/created.
    - ssh_client (paramiko.SSHClient): An established SSH client for connecting to the remote server.
    """
    #print("chenrj ... create_remote_directory 1")
    try:
        #print("chenrj ... create_remote_directory 2")
        # Establish SSH connection
        #ssh_client.connect(hostname=ssh_client.get_transport().getpeername()[0])
        # Use private key authentication (if you have a private key file)
        #ssh_client.connect(hostname='lxbk0496.gsi.de', username='litv-exp', key_filename='/u/litv-exp/.ssh/id_rsa')
        # Check if the directory exists
        stdin, stdout, stderr = ssh_client.exec_command(f"[ -d '{remote_path}' ] && echo 'Exists' || echo 'Not exists'")
        
        # Read the command execution result
        result = stdout.read().decode().strip()
        #print("chenrj ... create_remote_directory 2: ",result)
        if result == 'Not exists':
            # If the directory does not exist, create it
            ssh_client.exec_command(f"mkdir -p {remote_path}")
            #print(f"Created remote directory: {remote_path}")
        else:
            print(f"Remote directory already exists: {remote_path}")
            #print("chenrj ... create_remote_directory 3")
            files = list_directory_contents(ssh_client, remote_path)
            return files
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        # Close the SSH connection
        return []
    #print("chenrj ... create_remote_directory 4")
    
def update_file_list_periodically(ssh,file_listbox_iq,default_path_ntcap_iq,file_extension_iq,file_listbox_luster_iq,default_path_luster_iq,file_listbox_sc,default_path_ntcap_sc,file_extension_sc,file_listbox_luster_sc,default_path_luster_sc, should_stop_sync):
    while True:
        # Add your code logic here
        print("Running update_file_list_periodically...")
        # Call your function
        update_file_list(file_listbox_iq,default_path_ntcap_iq,"synced_files_iq.txt",file_extension_iq)  # Update the file list in file_listbox_iq with default path
        update_file_list_ssh(file_listbox_luster_iq, ssh, default_path_luster_iq,"","") 
        update_file_list(file_listbox_sc,default_path_ntcap_sc,"synced_files_sc.txt",file_extension_sc)  # Update the file list in file_listbox_iq with default path
        update_file_list_ssh(file_listbox_luster_sc, ssh, default_path_luster_sc,"","")
        time.sleep(10)
        
######################################################################
def main():

    if len(sys.argv) != 2:
        print("Usage: queqiao <path_to_config_file>")
        sys.exit(1)        
    config_file_path = sys.argv[1]
    ## read default path
    paths_config = read_paths_config(config_file_path)
    luster_hostname = paths_config["luster_hostname"]
    luster_username = paths_config["luster_username"]
    luster_keyfilename = paths_config["luster_keyfilename"]
    
    default_path_ntcap_iq_label = paths_config["default_path_ntcap_iq_label"] 
    default_path_ntcap_iq = paths_config["default_path_ntcap_iq"]
    default_path_luster_iq_label = paths_config["default_path_luster_iq_label"]  
    default_path_luster_iq = paths_config["default_path_luster_iq"]
    default_path_ntcap_sc_label = paths_config["default_path_ntcap_sc_label"]
    default_path_ntcap_sc = paths_config["default_path_ntcap_sc"]
    default_path_luster_sc_label = paths_config["default_path_luster_sc_label"]     
    default_path_luster_sc = paths_config["default_path_luster_sc"]

    #synced_files_iq = "synced_files_rsa01.txt"
    #synced_files_iq_end = ".tiq"
    #synced_files_sc = "synced_files_rsa02.txt"
    #synced_files_sc_end = ".tiq"
    synced_files_iq = paths_config["synced_files_iq"]
    synced_files_iq_end = paths_config["synced_files_iq_end"]   
    synced_files_sc = paths_config["synced_files_sc"]
    synced_files_sc_end = paths_config["synced_files_sc_end"]   

    try:
        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use private key authentication (if you have a private key file)
        print("connecting ssh to ",luster_hostname,".")
        ssh.connect(hostname=luster_hostname, username = luster_username, key_filename=luster_keyfilename)
    except paramiko.AuthenticationException:
        print("The current host is not available. please try other hosts, such as: lxbk0495,lxbk0494...")
    except paramiko.SSHException as e:
        print(f"Unable to establish SSH connection: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Create remote directories (IQ and SC)
    files_luster_iq = create_remote_directory(default_path_luster_iq, ssh)
    files_luster_sc = create_remote_directory(default_path_luster_sc, ssh)
    
    # Create the main window
    root = tk.Tk()
    root.title("Copy data from ntcap to luster.")
    
    # Set the custom window size (width x height)
    window_width = 1500
    window_height = 800
    should_stop_sync = [True]

    command = f"rm -vf IQ*synced_files_iq.txt SC*synced_files_sc.txt"
    subprocess.run(command, shell=True, check=True)
    
    root.geometry(f"{window_width}x{window_height}")
    ## Create a Label for hostname
    comment_label_hostname = tk.Label(root, text="hostname:")
    comment_label_hostname.grid(row=0, column=0, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for hostname
    folder_entry_hostname = tk.Entry(root,width=70)
    folder_entry_hostname.grid(row=0, column=1, columnspan=2,padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_hostname.insert(0, luster_hostname)  # Insert the default path

    ## Create a Label for username
    comment_label_username = tk.Label(root, text="username:")
    comment_label_username.grid(row=1, column=0, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for username
    folder_entry_username = tk.Entry(root,width=70)
    folder_entry_username.grid(row=1, column=1, columnspan=2,padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_username.insert(0, luster_username)  # Insert the default path

    ## Create a Label for keyfilename
    comment_label_keyfilename = tk.Label(root, text="keyfilename:")
    comment_label_keyfilename.grid(row=2, column=0, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for keyfilename
    folder_entry_keyfilename = tk.Entry(root,width=70)
    folder_entry_keyfilename.grid(row=2, column=1, columnspan=2,padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_keyfilename.insert(0, luster_keyfilename)  # Insert the default path

    
    ## Create the "Start" button
    start_button = tk.Button(root, text="Start", command=lambda:sync_files_to_server(start_button,stop_button,folder_entry_ntcap_iq, folder_entry_luster_iq,folder_entry_ntcap_sc,folder_entry_luster_sc,default_path_ntcap_iq,default_path_luster_iq,file_listbox_iq,file_listbox_sc, reset_button, browse_button_ntcap_iq, browse_button_ntcap_sc, should_stop_sync, folder_entry_hostname, folder_entry_username, folder_entry_keyfilename,ssh,file_listbox_luster_iq,file_listbox_luster_sc,synced_files_iq,synced_files_iq_end,synced_files_sc,synced_files_sc_end))
    
    start_button.grid(row=0, column=3, padx=5, pady=10, sticky="w")  # Left-aligned
    
    ## Create the "Stop" button
    stop_button = tk.Button(root, text="Stop", command=lambda:stop_sync(stop_button,start_button,folder_entry_ntcap_iq,folder_entry_luster_iq,folder_entry_ntcap_sc,folder_entry_luster_sc,reset_button,browse_button_ntcap_iq,browse_button_ntcap_sc,should_stop_sync,file_listbox_iq,file_listbox_sc, folder_entry_hostname, folder_entry_username, folder_entry_keyfilename))
    stop_button.grid(row=1, column=3, padx=5, pady=10, sticky="w")  # Left-aligned
    
    ## Create the "Reset" button
    reset_button = tk.Button(root, text="Reset", command=lambda:reset_sync(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc))
    reset_button.grid(row=2, column=3, padx=5, pady=10, sticky="w")  # Left-aligned

    ## Create the "Reset simulated data" button
    reset_sim_button = tk.Button(root, text="Reset sim.", command=lambda:reset_sim(file_listbox_iq,default_path_ntcap_iq,file_listbox_sc,default_path_ntcap_sc))
    reset_sim_button.grid(row=0, column=7, padx=5, pady=10, sticky="w")  # Left-aligned
    
    ## Create a Label for ntcap_iq
    comment_label_ntcap_iq = tk.Label(root, text=default_path_ntcap_iq_label)
    comment_label_ntcap_iq.grid(row=3, column=0, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for ntcap_iq
    folder_entry_ntcap_iq = tk.Entry(root,width=70)
    folder_entry_ntcap_iq.grid(row=3, column=1, columnspan=2,padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_ntcap_iq.insert(0, default_path_ntcap_iq)  # Insert the default path
    
    ## Create a Label for luster_iq
    comment_label_luster_iq = tk.Label(root, text=default_path_luster_iq_label)
    comment_label_luster_iq.grid(row=4, column=0, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for luster_iq
    folder_entry_luster_iq = tk.Entry(root,width=70)
    folder_entry_luster_iq.grid(row=4, column=1, columnspan=2,padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_luster_iq.insert(0, default_path_luster_iq)  # Insert the default path
    
    ## Create the file listbox
    file_listbox_iq = tk.Listbox(root, width = 30,height=25)  # Adjust the height as needed
    file_listbox_iq.grid(row=5, column=1, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create a vertical scrollbar for the file listbox
    file_listbox_iq_scrollbar = tk.Scrollbar(root, orient="vertical")
    file_listbox_iq_scrollbar.grid(row=5, column=1, sticky="nse")  # Right-aligned
    # Associate the scrollbar with the file listbox
    file_listbox_iq.config(yscrollcommand=file_listbox_iq_scrollbar.set)
    file_listbox_iq_scrollbar.config(command=file_listbox_iq.yview)
    update_file_list(file_listbox_iq,default_path_ntcap_iq,synced_files_iq,synced_files_iq_end)  # Update the file list in file_listbox_iq with default path
    
    ## Create the file listbox
    file_listbox_luster_iq = tk.Listbox(root, width = 30,height=25)  # Adjust the height as needed
    file_listbox_luster_iq.grid(row=5, column=2, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create a vertical scrollbar for the file listbox
    file_listbox_luster_iq_scrollbar = tk.Scrollbar(root, orient="vertical")
    file_listbox_luster_iq_scrollbar.grid(row=5, column=2, sticky="nse")  # Right-aligned
    # Associate the scrollbar with the file listbox
    file_listbox_luster_iq.config(yscrollcommand=file_listbox_luster_iq_scrollbar.set)
    file_listbox_luster_iq_scrollbar.config(command=file_listbox_luster_iq.yview)
    update_file_list_ssh(file_listbox_luster_iq, ssh, default_path_luster_iq,"","") 
    
    
    ## Create a Label for ntcap_sc
    comment_label_ntcap_sc = tk.Label(root, text=default_path_ntcap_sc_label)
    comment_label_ntcap_sc.grid(row=3, column=4, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for ntcap_sc
    folder_entry_ntcap_sc = tk.Entry(root,width=70)
    folder_entry_ntcap_sc.grid(row=3, column=5,columnspan=2, padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_ntcap_sc.insert(0, default_path_ntcap_sc)  # Insert the default path

    ## Create a Label for luster_sc
    comment_label_luster_sc = tk.Label(root, text=default_path_luster_sc_label)
    comment_label_luster_sc.grid(row=4, column=4, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create an Entry widget for luster_sc
    folder_entry_luster_sc = tk.Entry(root,width=70)
    folder_entry_luster_sc.grid(row=4, column=5, columnspan=2,padx=10, pady=10, sticky="w")  # Left-aligned
    folder_entry_luster_sc.insert(0, default_path_luster_sc)  # Insert the default path
    
    ## Create the file listbox
    file_listbox_sc = tk.Listbox(root, width = 30,height=25)  # Adjust the height as needed
    file_listbox_sc.grid(row=5, column=5, padx=10, pady=10, sticky="ns")  # Left-aligned
    # Create a vertical scrollbar for the file listbox
    file_listbox_sc_scrollbar = tk.Scrollbar(root, orient="vertical")
    file_listbox_sc_scrollbar.grid(row=5, column=5, sticky="nse")  # Right-aligned
    # Associate the scrollbar with the file listbox
    file_listbox_sc.config(yscrollcommand=file_listbox_sc_scrollbar.set)
    file_listbox_sc_scrollbar.config(command=file_listbox_sc.yview)
    update_file_list(file_listbox_sc,default_path_ntcap_sc,synced_files_sc,synced_files_sc_end)  # Update the file list in file_listbox_iq with default path
    
    ## Create the file listbox
    file_listbox_luster_sc = tk.Listbox(root, width = 30,height=25)  # Adjust the height as needed
    file_listbox_luster_sc.grid(row=5, column=6, padx=10, pady=10, sticky="w")  # Left-aligned
    # Create a vertical scrollbar for the file listbox
    file_listbox_luster_sc_scrollbar = tk.Scrollbar(root, orient="vertical")
    file_listbox_luster_sc_scrollbar.grid(row=5, column=6, sticky="nse")  # Right-aligned
    # Associate the scrollbar with the file listbox
    file_listbox_luster_sc.config(yscrollcommand=file_listbox_luster_sc_scrollbar.set)
    file_listbox_luster_sc_scrollbar.config(command=file_listbox_luster_sc.yview)
    update_file_list_ssh(file_listbox_luster_sc, ssh, default_path_luster_sc,"","")
    # Create a "Browse" button for folder selection
    browse_button_ntcap_iq = tk.Button(root, text="Browse", command=lambda: browse_folder_and_update_list_filebox(folder_entry_ntcap_iq, folder_entry_luster_iq, default_path_ntcap_iq, default_path_luster_iq, file_listbox_iq,ssh,file_listbox_luster_iq, synced_files_iq,synced_files_iq_end))
    browse_button_ntcap_iq.grid(row=3, column=3, padx=10, pady=10, sticky="w")  # Left-aligned
    
    # Create a "Browse" button for folder selection
    browse_button_ntcap_sc = tk.Button(root, text="Browse", command=lambda: browse_folder_and_update_list_filebox(folder_entry_ntcap_sc, folder_entry_luster_sc, default_path_ntcap_sc, default_path_luster_sc, file_listbox_sc,ssh,file_listbox_luster_sc,synced_files_sc,synced_files_sc_end))
    browse_button_ntcap_sc.grid(row=3, column=7, padx=10, pady=10, sticky="w")  # Left-aligned
    
    # Run the main loop
    root.mainloop()
    
if __name__ == "__main__":    
    main()
