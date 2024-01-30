import schedule
import datetime
import time
import import_export
import Plotting
import warnings

warnings.filterwarnings('ignore')

#run scheduler
def job():

    #import data
    facility_df,gran_df = import_export.import_data()
    #plot and save
    Plotting.save_all(facility_df, gran_df)
    #export to telegram
    img_name = ['choropleth.png','average_time_series.png','doughnut.png','latest_donation.png']
    img_note = ['This is the choropleth map that shows the trend on Blood donation for every state, the darker it is, the highe the number of blood donation in that state.',
                'The time series plot shows the average number of blood donation in each month for each type of blood for the last 15 months.',
                'The dougnut chart shows the percentage of blood donor in Malaysia whether they only donated blood once or more than once.',
                'The bar chart shows the latest date of blood donation for each age group.']
    for image,text in zip(img_name,img_note):
        import_export.send_telegram_message(text)
        import_export.send_telegram_image(img_path=f'./Output Image/{image}')

    Current_Date = datetime.datetime.today().date()
    current_time = datetime.datetime.today().strftime(r'%H:%M')
    import_export.send_telegram_message(f'Here is the Daily Update on Blood Donations in Malaysia with the latest data updated on {Current_Date} at {current_time}')

schedule.every().day.at('16:00').do(job)
while True:
    schedule.run_pending()
    time.sleep(1)

# schedule.run_all()#testing