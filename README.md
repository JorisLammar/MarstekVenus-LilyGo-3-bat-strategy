# MarstekVenus-LilyGo-3-bat-strategy
Home Assistant code for charging/discharging strategy for 3 Marstek batteries in a 3-phase electricity network

This is a charge/discharge strategy for 3 Marstek batteries in a 3-phase electricity network. 
Equally distributing the required power settings over the 3 batteries is not always a efficient strategy, as the efficiency of charging and discharging is less when using low power settings (up to 30% efficiency loss).
Therefor, this strategy will focus on maximum power use per battery. If a new battery needs to be involved, the process will take the inbalance of the power phases into account. Batteries that are 15% of their cutoff capacity, will get lower priority. This will avoid that one battery is fully loaded (or empty) in case you need the power capacity of the 3 batteries.
Also, batteries that are left behind (less than 10% of their cutoff capacity) will get higher priority if there are batteries that are more than 15% of their cutoff capacity. 
E.g. during discharge, it there is one or more batteries with a state of charge higher than 90% (assuming cutoff charge at 100%, which can be changed per battery), batteries with a state of charge lower than 85% will get lower priority. The first 800W (assuming max discharge power of 800W, which can be changed per battery) will go to the battery with a state of charge higher than 90%. The remaining required discharging power will go to the other batteries, in order of descending state of charge.

The calculation of the power settings is running in a pyscript (python)
If you don't have installed pyscript, look for pyscript in the add-on store and install the add-on. Scripts are stored in a subfolder config/pyscript. With the Studio Code Server, it is easy to handle the code.

Steps:
1. Make a helper (input_text) called batcalctemp
2. Copy the python script bat_calc in the config/pyscript folder.
3. Change the code (between line 40 en 72) to adapt to your entities
	a. Power usage
	b. Power usage per phase (in the same order as how the batteries are assigned to the phases).
	e.g. if battery1 is assigned to phase1, battery2 is assigned to phase 3 en battery3 is assigned to phase2. fase[0] is according to l1, fase[1] to l3 and fase[2] to l2.
	c. Battery_state_of_charge, charging_cutoff_capacity, discharging_cutoff_capacity, max_charge_power and max_discharge_power of each battery
4. Copy the 'steering battery' YAML script in a new script and give it a proper name (you need that name later in adapting the master automation that is guarding the script.
5. Change also the YAML code of the script to adapt to your entities
	a. Second step before the loop: stop all batteries
	b. First action of the loop, refresh the power usage of your p1 meter
	c. Third action, the last variabel 'switch' needs to be adjusted with the correct entity names of the forcible_charge_discharge settings of each battery
	d. Same for the next statements: setting the charging or discharging power and forcible_charge_discharge settings for each battery. The forcible_charge_discharge setting will be changed only if it is really changed. This will save time on the RS232 interface.
	e. Start running the script. The script runs 24000 iterations, which is about 43 hours.
6. Copy the 'master steering battery' YAML code to a new automation. Change the name of the script in the code according to the name you gave in step 4.

Remarks:
1. If one or more batteries changes to another active state (charge or discharge), the script will wait 12 seconds. The batteries needs the time to reach the new power settings. Otherwise the settings will overshoot and after 3 or 4 iterations get stable.
Eg. Power consumption is -1000W, which means there is a potential of 1000W charging. After 6 seconds, the power consumption will be -400W, which will be added to the already 1000W charging power, resulting in 400W power consumption 6 seconds later. The 400W will be subtracted again in the next iteration.
2. The 6,5 seconds wait between the iterations is based on some test periods. Faster iterations can result in overshooting behavior. But you can try to test with faster iterations. 
3. The discharging_cutoff_capacity is 12% and can't be set lower. This will result in a cutoff during discharge at 0,61 kWh in stead of 0,56 kWh. The advantage is that the battery will not consume 5W when total empty. If you want the battery to be discharged to 0,56kWh, you can change the cutoff capacity hard-coded to 11%.
4. You can tweak by changing the cutoff capacity and max_power settings of each battery individual. The python code should take these values into account.
5. Suggestions for improvements are always welcome.


