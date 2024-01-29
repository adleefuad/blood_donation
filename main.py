import schedule
import time
import import_export
import Plotting
import warnings

# warnings.ignore('ignore')

#run scheduler
def job():

    #import data
    facility_df,gran_df = import_export.import_data()
    #plot and save
    Plotting.save_all(facility_df, gran_df)
    #export to telegram
    img_name = ['choropleth.png','average_time_series.png','doughnut.png','latest_donation.png']
    for image in img_name:
        import_export.send_telegram_image(img_path=f'./Output Image/{image}')
    
    import_export.send_telegram_message('Here is the Daily Update on Blood Donations in Malaysia')

schedule.every().day.at('16:00').do(job)
while True:
    schedule.run_pending()
    time.sleep(1)

# schedule.run_all()#testing