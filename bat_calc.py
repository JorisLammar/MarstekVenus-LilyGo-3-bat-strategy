@service
def bat_calc():
    #This procedure calculates the preferred power settings for 3 Marstek Venus
    #batteries working in a 3-phase electricity connection. Every battery is connected
    #to one phase. The ordering of the phases and the batteries needs to be respected
    #(see some statements further when retrieving the current power usage per phase).
    #Because the efficiency is lower at low power usage, it will not divide an equal part 
    #over the 3 batteries, but try to use a maximum power before using a second or third battery.
    #
    #In the preparing step, based on the current power usage, it will be
    #determined whether we need to charge or discharge and what the difference (delta)
    #is to be added or substracted from the current settings. The current power settings
    #are stored in a temporary string variabel (batcalctemp), because it takes a longer period to
    #read the current power settings from the batteries. This allows faster iterations.

    #This procedure works in 4 steps. In the first step, the delta power usage will be
    #distributed over the batteries that are already in use. In case of substracting the difference
    #the battery with the lowest power setting will be used first. In case of adding differences, 
    #the battery with the highest power usage will be used first.
    #In the second step, the remaining delta will be assigned to the unused battery connected to
    #the phase that is in unbalance (in descending order)
    #In the first two steps, batteries that are 15% from charging or discharing cut off capacity
    #will be excluded. This is to avoid that one battery will be favored and fully charged or discharged. 
    #In a latter case, where the full power of the 3 batteries are needed, we try to avoid a battery that 
    #will be not available.
    #also in order to have a smooth distribution of the 3 batteries
    #  if there are batteries 10% from their cutoff capacity, batteries with more than 15%
    #  of their cutoff capacity will be stopped and excluded from the first phase.
    #  The second step to assign batteries based on phase unbalance will be skipped and in the
    #  third step, batteries close to the cutoff capacity will be picked up first.
    #In the third step, the batteries there were excluded (because they are almost fully charged or discharged),
    #the remaining delta will be assigned with lowest/highest capacity in charge/discharge first
    #In the last step, if the power usage of a battery is lower than 500W, we try to combine this with a battery
    #with a higher power usage.

    #In the next lines, information is retrieved from the power usage and batteries. This statements need
    #to be adjusted to your entities.

    #retrieve the current power usage
    verbruik = float(sensor.p1_meter_5c2faf051580_active_power)

    #and retrieve also the power usage per phase. Respect the order of the batteries that are assigned
    #to the different phases. In the example below, the first battery is coupled to the first phase, the third 
    #battery is coupled to the second phase and the second battery is coupled to the third phase.
    fase = [float(sensor.p1_meter_5c2faf051580_active_power_l1)]
    fase.append(float(sensor.p1_meter_5c2faf051580_active_power_l3))
    fase.append(float(sensor.p1_meter_5c2faf051580_active_power_l2))

    #retrieve the current state or charge of the batteries
    bat_pct = [float(sensor.lilygo_bat1_marstek_battery_state_of_charge)]
    bat_pct.append(float(sensor.lilygo_bat2_marstek_battery_state_of_charge))
    bat_pct.append(float(sensor.lilygo_bat3_marstek_battery_state_of_charge))

    #The charging cutoff capacity of the batteries
    bat_max_pct = [float(number.lilygo_bat1_marstek_charging_cutoff_capacity)]
    bat_max_pct.append(float(number.lilygo_bat2_marstek_charging_cutoff_capacity))
    bat_max_pct.append(float(number.lilygo_bat3_marstek_charging_cutoff_capacity))

    #and the discharging cutoff capacity
    bat_min_pct = [float(number.lilygo_bat1_marstek_discharging_cutoff_capacity)]
    bat_min_pct.append(float(number.lilygo_bat2_marstek_discharging_cutoff_capacity))
    bat_min_pct.append(float(number.lilygo_bat3_marstek_discharging_cutoff_capacity))

    #the maximum charging power per battery
    bat_max_power = [float(number.lilygo_bat1_marstek_max_charge_power)]
    bat_max_power.append(float(number.lilygo_bat2_marstek_max_charge_power))
    bat_max_power.append(float(number.lilygo_bat3_marstek_max_charge_power))

    #and the maximum dischargig power per battery
    bat_min_power = [float(number.lilygo_bat1_marstek_max_discharge_power)]
    bat_min_power.append(float(number.lilygo_bat2_marstek_max_discharge_power))
    bat_min_power.append(float(number.lilygo_bat3_marstek_max_discharge_power))

    #in order to have fast iterations, the power settings are not retrieved from
    #the batteries, but are stored (in a previous iteration at the end of this procedure)
    #in a input_text helper, called batcaltemp. 
    batcalctemp = str(input_text.batcalctemp)
    #the first character contains the general state: c for charge, d for discharge or s for stop.
    #all batteries have the same state, unless they are stopped.
    old_state = batcalctemp[0]
    #the next 3 characters contains the state (charge/discharge/stop) per battery
    state = [batcalctemp[1]]
    state.append(batcalctemp[2])
    state.append(batcalctemp[3])
    #in the remaining characters or the string are the currect power settings per battery stored
    power = [int(batcalctemp[4:8])]
    power.append(int(batcalctemp[8:12]))
    power.append(int(batcalctemp[12:16]))

    #in order to work generic we use dir_state as positive for charging and negative
    #for discharging. dir_delta will be used for positive delta (adding the delta to the
    #current power settings) or negative delta (substracting).
    #The are main four cases: charging/discharing, adding/substracting the current power usage
    #max_bat is the cutoff-capacity (in both cases charging/discharging)
    #min_bat will be used to determine batteries that are behind an equal distribution
    #the correction is the difference between the preset power and the real used power
    #for high power usages, it is about 4.5% for charging and 2.5% for discharging, for lower it is much higher. 
    #In this cases, the correct setting of power will be reached in two iterations
    dir_state = 1
    max_bat = bat_max_pct
    min_bat = bat_min_pct
    correction = 1.045
    count_low = 0
    if old_state == "d":
        dir_state = -1
        correction = -0.975
        max_bat = [-bat_min_pct[0], -bat_min_pct[1], -bat_min_pct[2]]
        min_bat = [-bat_max_pct[0], -bat_max_pct[1], -bat_max_pct[2]]

    #if the battery is empty (discharge) or full (charge), the current power setting will
    #be corrected to 0 (charging a full battery at 2500W setting has zero effect)
    #if the battery is almost full (charging) or empty (discharging), the 
    #current power setting will be added to the current power usage and the setting will be
    #set to 0 (see above why, this batteries are excluded from the first two steps)
    #if batteries are too low/high (10% from the discharge/charge cutoff, in case of charging/discharge)
    #batteries that are more than 15% above that cutoff point, will be put to 0 so that the other batteries
    #will be prioritized in the third step. The second step will not be executed (prio on phase)
    for i in range(3):
        if dir_state * bat_pct [i] >= max_bat[i]: 
            power[i] = 0
        if dir_state * bat_pct [i] >= (max_bat[i] - 15):
            verbruik = verbruik - correction * power[i]
            power[i] = 0
        if dir_state * bat_pct[i] < min_bat[i] + 10:
            count_low += 1

    #if batteries are left behind (too full during discharge or too empty during charge), batteries further
    #from the cutoff will be stopped
    phase_step = "y"
    if count_low > 0:
        for i in range(3):
            if dir_state * bat_pct[i] > min_bat[i] + 15:
                phase_step = "n"
                verbruik = verbruik - correction * power[i]
                power[i] = 0

    #in case of charging, when the capacity is above 95%, the real power usage is 1250W (if higher in preset)
    if old_state == "c":
        for i in range(3):
            if bat_pct[i] >= 95 and power[i] > 1250:
                power[i]=1250

    #check wether the new state will be charging or discharging. Take into account that
    #negative power usage (verbruik) means that there an overshoot of injecting power (solar cells or batteries)
    #I have noticed a difference of 4% real power usage versus the preset power usage (and higher at lower power usage)
    #this will be corrected to determine the delta (difference) in the required new power settings.
    old_power = power[0] + power[1] + power[2]
    if (old_power * dir_state < verbruik): 
        new_state = "d"
        delta = int(verbruik * 1.026)
    else:
        new_state = "c"
        delta = int(verbruik * (-0.957))

    #in case the state is changing (from charging to discharge or vice-versa), we start to assign to power settings from
    #scratch (the current power settings will be added to the current power usage to determine the total of power settings).
    #because the power settings are set to zero, this batteries will be excluded from the first step.
    if old_state != new_state:
        delta = delta - old_power
        power[0]=0
        power[1]=0
        power[2]=0
        #in case the remaining to distribute power usage is less than 30W, all batteries will be stopped (in order to
        #avoid toggling from charge to discharge or vice-versa)
        if delta < 30:
            delta = 0
            new_state = "s"

    #these parameters will be set in order to work generic in all cases (charge/discharge, add/substract delta)
    dir_state = 1
    max_bat = bat_max_pct
    max_power = bat_max_power
    dir_delta = 1
    if new_state == "d":
        dir_state = -1
        max_bat = [-bat_min_pct[0], -bat_min_pct[1], -bat_min_pct[2]]
        max_power = bat_min_power
    if delta < 0:
        dir_delta = -1
        max_power = [0, 0, 0]

    #first step: distribute the delta over the active batteries, in highest power setting for adding delta, lowest power setting
    #in subtracting delta.
    i = 0
    while i<3 and delta != 0: 
        high = -1
        high_power = (dir_delta - 1) * 2000

        #look for the active (power setting > 0) battery with the highest (lowest) power setting, 
        #taking into account that battery is not full (empty) (in case of adding delta)
        #and the power setting is not already the maximum allowed (in case of adding delta)
        for j in range(3):
            if dir_delta * power[j] > high_power and (dir_state * bat_pct[j] < (max_bat[j] +1 - dir_delta)) and dir_delta * power[j] < max_power[j]:
                high = j
                high_power = power[j]

        #if there is candidate battery to take some delta, check whether the maximum power setting is not exceeded.
        if high >= 0:
            new_power = min(max_power[high], (power[high] + delta) * dir_delta)
            delta = delta + power[high] - dir_delta * new_power
            power[high] = dir_delta * new_power

        i += 1

    #second step: in case there is some delta left, distribute the remaining delta on the inactive
    #batteries according to the highest inbalance of the phases. In this case, the delta is always positive.
    #if the current power settings were lower than the current power usage, the state will be switched and
    #the total power (always positive) will be assigned from scratch.
    #this step will be skipped if there are batteries left behind other (see higher)
    if phase_step == "y":
        i = 0
        while i<3 and delta != 0:
            high = -1
            high_power = 100000

            #look for the lowest/highest power usage phase (charging/discharge)
            #exclude batteries that are almost full/empty (charging/discharge)
            for j in range(3):
                if dir_state * fase[j] < high_power and dir_state * bat_pct[j] < (max_bat[j]-15) and power[j] == 0:
                    high = j
                    high_power = power[j]

            #if there is candidate battery to take some delta, check whether the maximum power setting is not exceeded.
            if high >= 0:
                new_power = min(max_power[high], delta)
                delta = delta - new_power
                power[high] = dir_delta * new_power

            i += 1

    #third step: in case there is still some remaining delta, we now use the batteries that are almost 
    #empty/full (charge/discharge)
    i = 0
    while i<3 and delta != 0:
        high = -1
        high_pct = 100

        #assign the remaining delta power to the battery with the lowest/highest state of charge (charge/discharge)
        for j in range(3):
            if dir_state * bat_pct[j] < high_pct and dir_state * bat_pct[j] < max_bat[j] and power[j] == 0:
                high = j
                high_pct = bat_pct[j]

        #if there is candidate battery to take some delta, check whether the maximum power setting is not exceeded.        
        if high >= 0:
            new_power = min(max_power[high], delta)
            delta = delta - new_power
            power[high] = dir_delta * new_power

        i += 1

    #fourth/last step: in case of power settings lower than 500W, try to combine with a battery with higher power settings
    high = -1
    high_power = 0
    low = -1
    low_power = 2500
    for i in range(3):
        if power[i] > high_power:
            high = i
            high_power = power[i]
        if (power[i] < low_power) and (power[i] > 0):
            low = i
            low_power = power[i]

    #in case such 2 batteries excist, add the lowest to the highest in case it doesn't exceed
    #the max power settings. Otherwise assign the average power settings to both.
    if low_power < 500 and high != low and high != -1 and low != -1:

        max_power = bat_max_power
        if new_state == "d": max_power = bat_min_power

        new_power = power[low] + power[high]
        if new_power > max_power[high]:
            power[low] = int(new_power/2)
            power[high] = int(new_power/2) 
        else:
            power[low]=0
            power[high]= new_power

    #check now whether batteries should be stopped (full/empty or zero power setting)
    count = 0
    for i in range(3):
        if (dir_state * bat_pct[i] >= max_bat[i]) or power[i] == 0:
            state[i] = "s"
            count += 1
        else:
            state[i] = new_state

    #if all batteries will be stopped, the general state is also "stop"
    if count == 3:
        new_state = "s"

    #store the output in the helper 
    input_text.batcalctemp = new_state + state[0] + state[1] + state[2] + convert_s(power[0]) + convert_s(power[1]) + convert_s(power[2])

def convert_s(val):

    result = "000" + f'{int(val)}'
    a = len(result)
    return result[a-4:a]
