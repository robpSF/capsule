import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry_convert as pc


continents = {"OC":"Australasia", "EU": "Europe",
              "NA": "North America","SA": "South America",
              "AS": "Middle East", "AF": "Africa"}

months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

#--------------------------------------------------------------------
#  missing_data
#
# this function removes rows from the dataframe where data is missing in a specific column
# and returns a dataframe which is a subset with only good data (ie the rows with missing data deleted)
#
def missing_data(df,column_header,error_text):
    # first create a copy because not all rows will have Locations unfortunately
    df2 = df
    # remove rows where country is missing
    df2 = df2.dropna(subset=[column_header])
    # report how many deleted
    diff = len(df) - len(df2)
    if diff > 0:
        st.subheader(error_text+": " + str(diff))
    return df2
#------------------------------------------------------------------------

# expects an Excel file exported from Capsule

# Read the Excel file into a pandas DataFrame
capsule_file = st.file_uploader("Enter Capsule XLSX file")

fy_start = st.sidebar.selectbox("Start of financial year",months)
fy_start_month = months.index(fy_start)+1

st.sidebar.write("If you want revenue, upload a pricing file.")
st.sidebar.write("Expecting file with 2 columns, 'Licence' and 'Price'")
pricing_file = st.sidebar.file_uploader("Enter pricing file XLSX file")

show_country_data = st.checkbox("Show Country Data")
show_licence_data = st.checkbox("Show Licence Data")
show_renewals = st.checkbox("Show Renewal Data")
show_interests = st.checkbox("Show Sector & Interests Data")
show_origin = st.checkbox("Show Origin story")

if capsule_file != None:
    df = pd.read_excel(capsule_file)

    go=st.button("go")

    if show_interests:
        # first create a copy because not all rows will have licences
        df2 = missing_data(df, "Sector/Industry", "Number of clients WITHOUT Sector/Industry details")

        df_sector = df2['Sector/Industry'].value_counts().reset_index()
        df_sector.columns = ['Sector/Industry', 'Count']
        fig = px.pie(df_sector, values='Count', names='Sector/Industry', title='Clients by Sector/Industry', hole=0.4)
        st.plotly_chart(fig)


        df2 = missing_data(df, "Interest/Exercises", "Number of clients WITHOUT Interest/Exercises details")
        df_sector = df2['Interest/Exercises'].value_counts().reset_index()
        df_sector.columns = ['Interest/Exercises', 'Count']
        fig = px.pie(df_sector, values='Count', names='Interest/Exercises', title='Clients by Interest/Exercises', hole=0.4)
        st.plotly_chart(fig)

    if show_origin:
        df2 = missing_data(df, "Origin", "Number of clients WITHOUT Origin details")
        df_sector = df2['Origin'].value_counts().reset_index()
        df_sector.columns = ['Origin', 'Count']
        fig = px.pie(df_sector, values='Count', names='Origin', title='Clients by Origin', hole=0.4)
        st.plotly_chart(fig)

        df_quarterly_origin = df2.groupby([pd.Grouper(key='renewal_date', freq=pd.offsets.QuarterBegin(startingMonth=fy_start_month)),"Origin"]).size().reset_index(name="Renewals")
        #st.dataframe(df_quarterly_origin)
        fig = px.bar(df_quarterly_origin, x='renewal_date', y='Renewals', color='Origin', barmode='group', title='Origin by quarter')
        st.plotly_chart(fig)

    # create new columns for country codes and continent
    if show_country_data:
        # first create a copy because not all rows will have Locations unfortunately
        df2 = df
        # remove rows where country is missing
        df2 = df2.dropna(subset=['Country'])
        # report how many deleted
        diff = len(df) - len(df2)
        if diff>0:
            st.subheader("Number of clients WITHOUT country details: "+str(diff))

        #do some country magic to group into continents
        df2['CountryCode'] = df2['Country'].apply(lambda x: pc.country_name_to_country_alpha2(x))
        df2['Continent'] = df2['CountryCode'].apply(lambda x: pc.country_alpha2_to_continent_code(x))
        df2['Continent'] = df2['Continent'].map(continents)

        df_Continent = df2['Continent'].value_counts().reset_index()
        df_Continent.columns = ['Continent', 'Count']
        fig = px.pie(df_Continent, values='Count', names='Continent', title='Clients by Continent', hole=0.4)
        st.plotly_chart(fig)

        df_Location = df['Country'].value_counts().reset_index()
        df_Location.columns = ['Country', 'Count']
        fig = px.pie(df_Location, values='Count', names='Country', title='Clients by Location', hole=0.4)
        st.plotly_chart(fig)
        st.table(df_Location)

        if pricing_file != None:
            st.subheader("Revenue by Location")
            df_pricing = pd.read_excel(pricing_file)
            df_revenue = pd.merge(df2, df_pricing, on='Licence')

            total_revenue = df_revenue.pivot_table(index='Continent', values='Price', aggfunc='sum')
            fig = px.pie(total_revenue, values='Price', names=total_revenue.index, title='Revenue by Continent', hole=0.4)
            st.plotly_chart(fig)

            total_revenue = df_revenue.pivot_table(index='Country', values='Price', aggfunc='sum')
            fig = px.pie(total_revenue, values='Price', names=total_revenue.index, title='Revenue by Country', hole=0.4)
            st.plotly_chart(fig)
            st.dataframe(total_revenue)

    if show_licence_data:
        # now look at licences
        # first create a copy because not all rows will have licences
        df2 = missing_data(df, "Licence", "Number of clients WITHOUT licence details")
        # remove rows where country is missing


        df_licence = df2['Licence'].value_counts().reset_index()
        df_licence.columns = ['Licence', 'Count']
        fig = px.pie(df_licence, values='Count', names='Licence', title='Licence count', hole=0.4)
        st.plotly_chart(fig)

        if pricing_file != None:
            df_pricing = pd.read_excel(pricing_file)
            df_revenue = pd.merge(df_licence, df_pricing, on='Licence')
            df_revenue['Revenue'] = df_revenue['Count'] * df_revenue['Price']
            total_revenue = df_revenue.groupby(['Licence']).sum()
            fig = px.pie(total_revenue, values='Revenue', names=total_revenue.index, title='Revenue by Licence', hole=0.4)
            st.plotly_chart(fig)
            #st.dataframe(total_revenue)
            #st.write(total_revenue['Revenue'].sum())

    if show_renewals:
        df2 = missing_data(df,"renewal_date","Number of clients with missing renewal dates")

        #convert the renewal_date column into a proper datetime type
        df2['renewal_date'] = pd.to_datetime(df2['renewal_date'])

        if pricing_file != None:
            df_pricing = pd.read_excel(pricing_file)
            df2 = pd.merge(df2, df_pricing, on='Licence')

        #st.write(df2)
        df3 = pd.DataFrame(df2, columns=["renewal_date","Licence","Price"])
        #st.write(df3)

        renewals_by_quarter = df3.groupby(
            pd.Grouper(key='renewal_date', freq=pd.offsets.QuarterBegin(startingMonth=fy_start_month))).count()
        #st.write(renewals_by_quarter)
        fig = px.bar(renewals_by_quarter, x=renewals_by_quarter.index, y='Licence',title="Licence renewals by quarter")
        st.plotly_chart(fig)

        df_quarterly_revenue = df3.groupby(pd.Grouper(key='renewal_date', freq=pd.offsets.QuarterBegin(startingMonth=fy_start_month)))['Price'].sum().reset_index()
        #st.write(df_quarterly_revenue)
        fig = px.bar(df_quarterly_revenue, x='renewal_date', y='Price',title="Licence revenue by Quarter")
        st.plotly_chart(fig)

