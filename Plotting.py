import pandas as pd 
import numpy as np 
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt 
import geopandas as gpd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from hospital import hospital_state

#get data and plot then save
def plot_choropleth(facility_df):
    #Process the data
    facility_df['state'] = facility_df['hospital'].map(hospital_state) # add state column from hospital_state
    facility_df['date']= pd.to_datetime(facility_df['date']) # set the column data type into pandas datetime
    latest_date = max(facility_df['date']) #Get the latest date in the dataframe
    last_49_days = latest_date-pd.Timedelta(days=49) #Get the date 49 days ago
    last49_df = facility_df[facility_df['date']>=last_49_days]
    state49_df = last49_df.groupby('state')['daily'].sum().reset_index(name='total_donation')

    #Process geojson data
    gdf = gpd.read_file('malaysia-with-regions_.geojson')
    gdf.drop(columns=['id','density','path'],axis=1,inplace=True)#drop other columns
    gdf.drop(index=[1,10],inplace=True)#drop Perlis and Putrajaya
    gdf.loc[0,'name'] = 'Kuala Lumpur' #rename Wilayah KL to Kuala Lumpur
    gdf.sort_values(by='name',inplace=True) #Sort by name
    gdf.reset_index(inplace=True,drop=True)#reset index

    #merge dataset
    state49_df_merged = gdf.merge(state49_df, how='left', left_on='name', right_on='state')
    state49_df_merged=state49_df_merged.iloc[:,1:]

    # Normalize Total Donation 
    vmin, vmax = state49_df_merged['total_donation'].min(), state49_df_merged['total_donation'].max()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    colour_gradient = 'Reds'

    # Create the main plot for Peninsular Malaysia excluding Kuala Lumpur for clarity
    fig, ax_main = plt.subplots(figsize=(16, 16))
    plt.text(x=103,y=6,s = 'Blood Donations by State for Last 49 days',fontsize = 20)
    plt.text(x=103,y=5.85,s = f'({last_49_days.date()}) - ({latest_date.date()})',fontsize = 'xx-large')
    peninsular_without_kl = state49_df_merged[(state49_df_merged['state'] != 'Sabah') & (state49_df_merged['state'] != 'Sarawak') & (state49_df_merged['state'] != 'Kuala Lumpur')]
    peninsular_without_kl.plot(column='total_donation', ax=ax_main, cmap=colour_gradient, norm=norm)

    # Create an inset for Sabah and Sarawak
    ax_sabah_sarawak = inset_axes(ax_main, width="150%", height="150%", loc='center left',
                                bbox_to_anchor=(1, 0.1, 1, 1), bbox_transform=ax_main.transAxes)
    sabah_sarawak = state49_df_merged[(state49_df_merged['state'] == 'Sabah') | (state49_df_merged['state'] == 'Sarawak')]
    sabah_sarawak.plot(column='total_donation', ax=ax_sabah_sarawak, cmap=colour_gradient,norm=norm)

    # Adjust Sabah and Sarawak plot (optional zoom and removing axis)
    ax_sabah_sarawak.set_xlim([sabah_sarawak.total_bounds[0], sabah_sarawak.total_bounds[2]])
    ax_sabah_sarawak.set_ylim([sabah_sarawak.total_bounds[1], sabah_sarawak.total_bounds[3]])
    ax_sabah_sarawak.set_frame_on(False)
    ax_sabah_sarawak.set_xticks([])
    ax_sabah_sarawak.set_yticks([])

    # Create an inset for Kuala Lumpur
    ax_kl = inset_axes(ax_main, width="15%", height="15%", loc='lower left',
                        bbox_to_anchor=(0.1, 0.1, 1, 1), bbox_transform=ax_main.transAxes)
    kl = state49_df_merged[state49_df_merged['state'] == 'Kuala Lumpur']
    kl.plot(column='total_donation', ax=ax_kl, cmap=colour_gradient,norm=norm)

    # Adjust Kuala Lumpur plot (optional zoom and removing axis)
    ax_kl.set_xlim([kl.total_bounds[0], kl.total_bounds[2]])
    ax_kl.set_ylim([kl.total_bounds[1], kl.total_bounds[3]])
    ax_kl.set_frame_on(False)
    ax_kl.set_xticks([])
    ax_kl.set_yticks([])

    # Remove axis for the main plot for a cleaner look
    ax_main.set_axis_off()

    # Add Label to the plot
    for idx, row in state49_df_merged.iterrows():
        
        # Get the position of the label
        x, y = row['geometry'].centroid.x, row['geometry'].centroid.y
        
        # Define the label text
        label_text = f"{row['state']}\n{row['total_donation']}\n{round(row['total_donation']/state49_df_merged['total_donation'].sum()*100,2)}%"
        # Place the label on the map
        if row['state'] == 'Kuala Lumpur':
            ax_kl.text(x-0.1, y+0.1, label_text, fontsize=12, ha='center', va='center',color='black')
        
        elif (row['state'] == 'Sarawak') | (row['state'] == 'Sabah'):
            ax_sabah_sarawak.text(x, y, label_text, fontsize=12, ha='center', va='center')
        
        else:
            ax_main.text(x, y, label_text, fontsize=12, ha='center', va='center')

    # save chart as image
    image_dir = r'./Output Image/'
    image_name = 'choropleth.png'
    plt.savefig(image_dir+image_name, bbox_inches='tight')
    print('Plotting and Save Choropleth Successful!')
    
def plot_average(facility_df):
    # Grouping data by date
    aggregated_data = facility_df.groupby('date')[['blood_a', 'blood_b', 'blood_ab', 'blood_o','daily']].sum()

    # Resampling the data to a monthly frequency and calculating the average daily donations for each blood type
    average_daily_per_month = aggregated_data.resample('ME').mean()

    # Selecting the last 15 months for comparison
    last_15_months_avg_daily = average_daily_per_month.last('15M')

    # Setting the style for the plot
    plt.rcParams.update({'font.family':'monospace'})

    # Creating a larger figure
    plt.figure(figsize=(18, 14))

    # Time Series Plot for each blood type with data labels
    for blood_type, color,blood_label in zip(['blood_a', 'blood_b', 'blood_ab', 'blood_o'], ['blue', 'green', 'red', 'purple'],['blood a', 'blood b', 'blood ab', 'blood o']):
        plt.plot(last_15_months_avg_daily.index, last_15_months_avg_daily[blood_type], label=blood_label, color=color, alpha=0.7)
        for x, y in zip(last_15_months_avg_daily.index, last_15_months_avg_daily[blood_type]):
            plt.text(x, y, f'{y:.1f}', color='black', fontsize=10)

    # Bar Chart Overlay for average daily donation of all types with data labels
    bar_width = 20  # days
    bars = plt.bar(last_15_months_avg_daily.index, last_15_months_avg_daily['daily'], width=bar_width, label='Average Daily - All Types', color='grey', alpha=0.5)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.1f}', va='bottom', ha='center', fontsize=10)

    plt.title('Monthly Average Daily Blood Donations by Type and Overall Average (Last 15 Months)', fontsize=14)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Average Daily Blood Donated per Month', fontsize=12)
    plt.xticks(last_15_months_avg_daily.index, rotation=45, fontsize=10)
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
     # save chart as image
    image_dir = r'./Output Image/'
    image_name = 'average_time_series.png'
    plt.savefig(image_dir+image_name, bbox_inches='tight')
    print('Plotting and Save AverageTime Series Successful!')

def gran_data_process(gran_df):
    gran_df['visit_date'] = pd.to_datetime(gran_df['visit_date']) #set date to datetime data type
    gran_df['donor_age'] = gran_df['visit_date'].dt.year-gran_df['birth_date'] #getting the age of donor at the date of donation
    gran_fil = gran_df[gran_df['donor_age']<=65] #Filter only take age 65 or less
    return gran_fil
def gran_data_process2(gran_df):
    gran_fil = gran_data_process(gran_df)
    donor_donations = gran_fil.groupby('donor_id').size().reset_index(name='donation_count')
    return donor_donations

def plot_doughnut(gran_df):
    donor_donations = gran_data_process2(gran_df)
    #binning the donation count
    count_bins = [1, 2, 4, 7, float('inf')]
    count_labels = ['New Donor','2-3 Donations','4-7 Donations','8+ Donations']
    donor_donations['donation_count_group'] = pd.cut(donor_donations['donation_count'],bins=count_bins,labels=count_labels,right=False)
    one_time_count = donor_donations[donor_donations['donation_count_group']=='New Donor']['donation_count_group'].count()
    repeater_count = donor_donations[donor_donations['donation_count_group']!='New Donor']['donation_count_group'].count()
    first_group = donor_donations[donor_donations['donation_count_group']=='2-3 Donations']['donor_id'].count()
    second_group = donor_donations[donor_donations['donation_count_group']=='4-7 Donations']['donor_id'].count()
    third_group = donor_donations[donor_donations['donation_count_group']=='8+ Donations']['donor_id'].count()

    #Plot a two level Pie Chart
    fig,ax = plt.subplots(figsize=(12,3))
    ax.axis('equal')
    width = 0.8

    plt.text(0, 4, 'Distribution of Blood Donor', horizontalalignment='center', verticalalignment='top', fontsize=20,)

    #label and size for outer donut chart
    sizes_out = [first_group,second_group,third_group,one_time_count]
    label_out = ['2-3','4-7','8+','1']

    #label and size for inner donut chart
    label_in = ['Repeater','One Time']
    sizes_in = [repeater_count,one_time_count]

    # Calculate the percentages for the outer ring
    percentages_out = [f"{(size / sum(sizes_out[0:3]) * 100):.1f}%" for size in sizes_out]

    # Update labels for the outer ring with percentages
    label_out_with_perc = [f"{label} ({perc})" for label, perc in zip(label_out, percentages_out)]
    label_out_with_perc[3] = '' #To make the 1 time donor invisible

    # Calculate the percentages for the inner ring
    percentages_in = [f"{(size / sum(sizes_in) * 100):.1f}%" for size in sizes_in]

    # Update labels for the inner ring with percentages
    label_in_with_perc = [f"{label} ({perc})" for label, perc in zip(label_in, percentages_in)]

    #Outer Ring (Donation Count Band)
    cm = plt.get_cmap("tab20c")

    cout = cm(np.array([9,10,11,13]))
    cout[3] = mcolors.to_rgba('white')  # Convert 'white' to RGBA
    pie, *_ = ax.pie(sizes_out, radius=3, labels=label_out_with_perc, colors=cout)
    plt.setp(pie, width=width, edgecolor='white',)

    #Inner Ring (Repeater Or Not)
    cin = cm(np.array([8,12]))
    pie2, *_= ax.pie(sizes_in, radius=3-width, labels=label_in_with_perc,
                    labeldistance=0.9, colors=cin,rotatelabels=0)
    plt.setp(pie2, width=width, edgecolor='white')

    image_dir = r'./Output Image/'
    image_name = 'doughnut.png'
    plt.savefig(image_dir+image_name, bbox_inches='tight')
    print('Plotting and Donor Distribution Successful!')

def plot_latest(gran_df):
    gran_fil = gran_data_process(gran_df)
    donor_donations = gran_data_process2(gran_df)
    #Getting all latest date donor
    latest_date = max(gran_fil['visit_date'])
    latest_donor = gran_fil[gran_fil['visit_date']==latest_date]
    latest_donor = latest_donor.merge(donor_donations[['donor_id', 'donation_count']], on='donor_id', how='left')
    # Rename the 'donation_count' column to 'donations_count'
    latest_donor.rename(columns={'donation_count': 'donations_count'}, inplace=True)
    #Binning the number of donation
    count_bins = [1, 2, 4, 7, float('inf')]
    count_labels = ['New Donor','2-3 Donations','4-7 Donations','8+ Donations']
    latest_donor['donations_count_group'] = pd.cut(latest_donor['donations_count'],
                                                    bins=count_bins,
                                                    labels=count_labels,
                                                    right=False)
    
    #Binning the age
    age_bins = [17, 24, 29, 34, 39, 44, 49, 54, 59, 65]
    age_labels = ['17-24','25-29','30-34','35-39','40-44','45-49','50-54','55-59','60-65']
    latest_donor['donor_age_group'] = pd.cut(latest_donor['donor_age'],bins=age_bins,labels=age_labels)
    grouped_data = latest_donor.groupby([ 'donor_age_group','donations_count_group']).size().unstack(fill_value=0)
    # Plot the stacked horizontal bar chart
    grouped_data.plot(kind='barh', stacked=True, figsize=(14, 8),cmap='YlGn')

    # Adding titles and labels
    plt.title(f'{latest_date.strftime("%d-%m-%Y")} Donation Frequency by Age & Donor Group', fontsize=15)
    plt.xlabel('Number of Donors', fontsize=15)
    plt.ylabel('Donation Count Group', fontsize=15)
    plt.legend(title='Age Group', bbox_to_anchor=(1.05, 1), loc='upper left')
    # save chart as image
    image_dir = r'./Output Image/'
    image_name = 'latest_donation.png'
    plt.savefig(image_dir+image_name, bbox_inches='tight')
    print('Plotting and Save Latest Donation Successful!')

def save_all(facility_df,gran_df):
    plot_choropleth(facility_df)
    plot_average(facility_df)
    plot_doughnut(gran_df)
    plot_latest(gran_df)