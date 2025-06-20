#Create webapp to visualize data dashboard for specific product for NOSE HERBALINDO
#WebApp Dashboard Project : 19 June 2025
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import csv
import regex as re

#Setting Page
def main():
    st.set_page_config(
        page_title = 'ExpertCare Sales Performance',
        layout = 'wide',
        initial_sidebar_state = "expanded"
    )

    #alt.themes.enable("dark")
    st.title('ExpertCare Sales Performance 2025')

    month_order = {
    1:'January',
    2:'February',
    3:'March',
    4:'April',
    5:'May',
    6:'June',
    7:'July',
    8:'August',
    9:'September',
    10:'October',
    11:'November',
    12:'December'
}
    df = pd.read_csv('D:/KERJAAN/NOSE HERBAL/ANALYSIS/ExpertCare/Clean_Shopee_16625.csv')

    df['month'] = pd.to_datetime(df['scraping_date']).dt.month

    df['month'] = df['month'].map(month_order)

    with st.sidebar:
        st.title('ExpertCare Product Sales Performance')

        #Create available month list for the visitor to choose
        month_list = df['month'].unique().tolist()

        #button mechanisms
        selected_month = st.selectbox('Select a month', month_list, index=len(month_list)-1)
        df_selected_month = df[df.month == selected_month]
        df_selected_month_sorted = df_selected_month.sort_values(by="Sales", ascending=False)

    #Create placeholder 
    sales_metric,revenue_metric,rating_metric = st.columns((2.5,2.5,1.5),gap='medium')

    #Create sales calculation function
    def calculate_sales_metric(month):
        sales_ = df.loc[df['month'] == month, 'Sales'].sum()
        return sales_
    
    #Create revenue calculation function
    def calculate_revenue_metric(month):
        total_revenue = df.loc[df['month']==month,'revenue'].sum()
        return total_revenue
    #Create rating calculation function
    def calculate_rating(month):
        average_rating = round(df.loc[df['month']==month,'Rating'].mean(),2)
        return average_rating

    #formatting number in metric viz
    def format_number(num):
        if num is None:
            return "-" 
        try:
            num = float(num)
        except (ValueError, TypeError):
            return str(num)

        if abs(num) >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}Bn"
        elif abs(num) >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        else:
            return f"{num:,.0f}"  # Format biasa dengan koma (misal: 12,500)

    st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
        font-size: 40px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def shorten_name(name, max_len=25):
        return name if len(name) <= max_len else name[:max_len]+ '...'
    
    df['short_name'] = df['Nama Produk'].apply(lambda x : shorten_name(x,25))
    with sales_metric:
        sales_selected_month = calculate_sales_metric(selected_month)
        #selected_month_num = {v: k for k, v in month_order.items()}[selected_month]
        #selected_month_before = selected_month_num - 1
        #month_before = df[selected_month_before].map(month_order)
        #sales_month_before = calculate_sales_metric(month_before)
        st.metric(label = f'Sales in {selected_month}', value = f'{format_number(sales_selected_month)} units')
    
    with revenue_metric:
        total_rev = calculate_revenue_metric(selected_month)
        st.metric(label=f'Total Revenue(Rp) in {selected_month}', value = f'{format_number(total_rev)} Rupiah')
    with rating_metric:
        rating = calculate_rating(selected_month)
        st.metric(label = f'Shop Rating in {selected_month}', value = rating)

    sales_histogram,rev_month=st.columns(2)

    def extract_min_price(price_str):
    # Ambil semua angka dari string (hilangkan titik dan koma)
        numbers = re.findall(r'\d[\d.]*', price_str.replace(',', '').replace('.', ''))
        if numbers:
            return int(numbers[0])
        return 0

    # Tambahkan kolom untuk sort
    df_selected_month['min_price'] = df_selected_month['price_bins'].apply(extract_min_price)
    df_seletced_month = df_selected_month.sort_values(by='min_price',ascending = True)

    #create histogram of sales distribution with certain range price
    #fig1 = Sales Distribution Based on Price Range
    #fig2 = Revenue MoM 
    with sales_histogram:
        df_sales_hist = df_selected_month.groupby('min_price').agg({
        'price_bins':'min',
        'Sales':'sum'
        }).reset_index()

        fig1 = px.bar(df_sales_hist,x = 'price_bins',y='Sales',color = 'price_bins',
                 color_discrete_sequence= px.colors.sequential.Plasma_r,text = 'price_bins')
        fig1.update_traces(marker_line_width=0,texttemplate="%{y}")
        fig1.update_layout(
            title = 'Customer Spending Range',
            xaxis = dict(
            title='Price Range',
            tickangle = 45,
            tickfont = dict(size=12),
            rangeslider=dict(visible=False)
            ),
            yaxis = dict(title='Customer Amount'),
            width = 500,
            height = 500,
            margin = dict(l=40,r=40,t=40,b=40),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with rev_month:
        df_total_rev = df_selected_month.groupby('month').agg({
            'revenue':'sum'
        }).reset_index()
        fig2 = px.line(df_total_rev, x = 'month', y='revenue', title = 'Revenue per Month(Rp)')
        st.plotly_chart(fig2, use_container_width=True)
    
    top_product_sales,top_product_revenue = st.columns(2)
    #Shorten product name, to wrap the text
    df_selected_month['short_name'] = df_selected_month['Nama Produk'].apply(lambda x:shorten_name(x,25))

    df_top_sales_rev = df_selected_month.groupby('short_name').agg({
        'Sales':'sum',
        'revenue':'sum'
    }).reset_index().sort_values(by= 'Sales',ascending = False)

    with top_product_sales:
        fig3 = px.bar(df_top_sales_rev,x = 'short_name', y = 'Sales',
                      color = 'Sales',labels = 'Nama Produk',
                 color_discrete_sequence= px.colors.sequential.Plasma_r,
                 text = 'Sales')
        fig3.update_traces(marker_line_width=0,texttemplate="%{y}")
        fig3.update_layout(
            title = 'Highest Performing Product Based on Monthly Sales',
            xaxis = dict(
            title='Product Name',
            tickangle = 90,
            tickfont = dict(size=12),
            rangeslider=dict(visible=False)
            ),
            yaxis = dict(title='Sales'),
            width = 1200,
            height = 500,
            margin = dict(l=40,r=40,t=40,b=40),
        )
        st.plotly_chart(fig3)

    with top_product_revenue:
        df_top_product_revenue = df_selected_month.groupby('short_name').agg(
            {
                'Nama Produk':'min',
                'revenue':'sum'
            }
        ).reset_index().sort_values(by='revenue', ascending = False)
        
        fig4 = px.bar(df_top_product_revenue,x = 'short_name',y = 'revenue',color = 'revenue',labels = 'Nama Produk', 
                      color_continuous_scale= px.colors.sequential.Viridis,
                      text = 'revenue')
        fig4.update_traces(marker_line_width=0, texttemplate="%{y}")
        fig4.update_layout(
            title = 'Revenue per Product (Rp)',
            xaxis = dict(
                title = 'Product Name', tickangle = 90, tickfont=dict(size=12),rangeslider=dict(visible=False)),
                yaxis = dict(title = 'revenue'),
                width = 1200,
                height = 500,
                margin = dict(l=40,r=40,t=40,b=40),
            )
        st.plotly_chart(fig4)

if __name__== '__main__':
    main()
