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
    facility_df['state'] = facility_df['hospital'].map(hospital_state) # add state column
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
        label_text = f"{row['state']}\n{row['total_donation']}"
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
    for blood_type, color in zip(['blood_a', 'blood_b', 'blood_ab', 'blood_o'], ['blue', 'green', 'red', 'purple']):
        plt.plot(last_15_months_avg_daily.index, last_15_months_avg_daily[blood_type], label=f'Blood Type {blood_type[-1]} - Time Series', color=color, alpha=0.7)
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
def save_all(facility_df,gran_df):
    plot_choropleth(facility_df)
    plot_average(facility_df)