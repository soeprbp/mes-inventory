================================================================
   MES INVENTORY SYSTEM  -  HOW TO USE THIS USB DRIVE
================================================================

WHAT THIS DOES:
This USB drive collects information about the computers and
machines on your factory floor. It runs from this USB stick —
nothing gets installed on the machines you scan.

This process takes about 5 to 15 minutes per machine,
depending on how many devices are on the network.


--------------------------------------------------------------
STEP 1 — SCAN A MACHINE
--------------------------------------------------------------

1. Plug this USB drive into the Windows computer you want to
   scan.

2. Open "This PC" or "My Computer" and double-click the USB
   drive to open it.

3. Open the folder called "MESInventory".

4. Double-click the file named "RunInventory.bat".

   → A black window will open and start collecting information.
     This is normal. Let it run.

5. When it finishes, the black window will say "Press any key
   to continue..." or it will close on its own.

6. Leave the USB plugged in and move to the next machine.
   Repeat steps 2-5 for each computer you need to scan.

   NOTE: You CAN scan more than one machine with this same USB.
   Just plug it into the next machine and run the same file
   again. The results will not overwrite each other.


--------------------------------------------------------------
STEP 2 — BRING THE USB BACK
--------------------------------------------------------------

When you have scanned all the machines you need to:

1. Safely remove the USB drive from the last machine.

2. Bring the USB back to your desk / workstation.

3. Give the USB to whoever manages the MES Inventory system
   (your IT contact or MES team).


--------------------------------------------------------------
WHAT IF SOMETHING GOES WRONG?
--------------------------------------------------------------

• If the black window closes immediately:
  That can happen on machines that are offline or not on the
  network. The scan still collected what it could from the
  local machine. This is OK — bring the USB back anyway.

• If you get a pop-up asking to "Allow access" or a firewall
  warning:
  Click "Allow access" or "Yes". The program needs to look at
  the network to find connected devices.

• If you get an error that says the program "can't run" or
  "is not compatible":
  Note the error message and tell your IT contact. The
  computer may be running a very old version of Windows.

• If you accidentally run the scan twice on the same machine:
  No harm done. The system will update the existing record
  with the newest information.


--------------------------------------------------------------
FILES ON THIS USB (for your reference)
--------------------------------------------------------------

RunInventory.bat   ← This is the one you double-click
collector.exe      ← Collects hardware & software info
netscan.exe        ← Scans the network for connected devices
combine.exe        ← Puts the results together
data/inventory/    ← Where the results are saved (do not edit)


--------------------------------------------------------------
QUESTIONS?
Contact the MES team or your IT department.
================================================================
