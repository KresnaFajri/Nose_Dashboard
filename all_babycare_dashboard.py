import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import regex as re

def main():
    st.set_page_config(
        page_title = 'Top 10 Baby Care Brands in Indonesia 2025',
        layout = 'wide',
        initial_sidebar_state = "expanded")
    
    st.title('Top 10 Baby Care Brands in Indonesia (2025)')

    placeholder = st.empty()

    #load the dataset
    @st.cache_data
    def load_data(url):
        df = pd.read_csv(url, on_bad_lines = 'skip')
        return df
    
    df = load_data('dataset/Clean Brand.csv')

    with st.sidebar:
        st.title('ExpertCare Product Sales Performance')

        #Create available month list for the visitor to choose
        month_list = df['month'].unique().tolist()

        #button mechanisms
        selected_month = st.selectbox('Select a month', month_list, index=len(month_list)-1)
        selected_brand = st.selectbox('Select a brand', df['brand'].unique().tolist())
        df_selected_month = df[df.month == selected_month]
        df_selected_brand = df[df.brand == selected_brand]

    #Month order to be used in the data viz
    filtered_df = df[(df['brand'] == selected_brand) & (df['month'] == selected_month)]

    def calculate_sales_metric(month,brand):
        sales = filtered_df['sales'].sum()
        return sales
    
    def calculate_revenue_metric(month,brand):
        revenue = filtered_df['revenue'].sum()
        return revenue
    
    def calculate_total_unique_product(month,brand):
        nunique_products = filtered_df['product_name'].nunique()
        return nunique_products
    
    def calculate_pct_revenue(df):
        df = df.copy()                        # hindari SettingWithCopy
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')

        total = df['revenue'].sum()

        if total == 0:
            df['pct_revenue'] = 0.0
        else:
            df['pct_revenue'] = (100*df['revenue'] / total ).round(2)
        return df
    
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
            return f"{num:,.0f}" 
    
    def shorten_name(name, max_len=25):
        return name if len(name) <= max_len else name[:max_len]+ '...'

    total_unique_product,amount_revenue_metric,amount_sales_metric, = st.columns(3)
    st.markdown("""<style>
    [data-testid="stMetricValue"] {
            font-size: 60px;
        }
        </style>
        """, unsafe_allow_html=True)
    with amount_sales_metric:
        sales_brand_month = calculate_sales_metric(selected_month,selected_brand)
        st.metric(label = f'Sales of {selected_brand} in {selected_month}', value = f'{format_number(sales_brand_month)} units')

    with amount_revenue_metric:
        revenue_brand_month = calculate_revenue_metric(selected_month,selected_brand)
        st.metric(label = f'Revenue of {selected_brand} in {selected_month}', value = f'{format_number(revenue_brand_month)} Rupiah')
    with total_unique_product:
        amount_unique_product = calculate_total_unique_product(selected_month, selected_brand)
        st.metric(label = f'Total Unique Products of {selected_brand} in {selected_month}', value = f'{amount_unique_product} unique products')

    sales_histogram, top_sales_products = st.columns(2)

   
    def extract_min_price(price_str):
    # Ambil semua angka dari string (hilangkan titik dan koma)
        numbers = re.findall(r'\d[\d.]*', price_str.replace(',', '').replace('.', ''))
        if numbers:
            return int(numbers[0])
        return 0
    
    filtered_df['min_price'] = filtered_df['Price Range'].apply(extract_min_price)
    filtered_df = filtered_df.sort_values(by='min_price',ascending = True)
    
    with sales_histogram:
        df_sales_hist = filtered_df.groupby('min_price').agg({
            'Price Range':'min',
            'sales':'sum'
        }).reset_index()

        fig_hist = px.bar(df_sales_hist, x = 'Price Range', y = 'sales', color = 'Price Range',
        color_discrete_sequence = px.colors.sequential.Plasma_r, text = 'Price Range')
        fig_hist.update_traces(marker_line_width = 0, texttemplate = "%{y}")
        fig_hist.update_layout(
            title = 'Sales per Price Range',
            xaxis = dict(
            title = 'Price Range(Rp)',
            tickangle = 90,
            tickfont = dict(size=12),
            rangeslider = dict(visible = False)
            ),
            yaxis = dict(title = 'Total Product Sold'),
            width = 500,
            height = 500,
            margin = dict(l =40,r =40, t=40, b = 40),)
        fig_hist.update_layout(bargap = 0.1)
        st.plotly_chart(fig_hist,use_container_width = True)
        
    with top_sales_products:
        filtered_df['short_name'] = filtered_df['product_name'].apply(lambda x:shorten_name(x,25))

        st.markdown("""
            <style>
            [data-testid="stMetricValue"] {
            font-size: 50px;
            }
            </style>
            """, unsafe_allow_html=True)

        df_top_product = filtered_df.groupby('short_name').agg({\
            'product_name':'min',
            'sales':'sum',
            'revenue':'sum'}).reset_index()
        
        fig_sales_product = px.bar(df_top_product,x='short_name',y='sales',title = 'Sales per Product',
                                      color = 'sales', labels = 'product_name',color_continuous_scale = px.colors.sequential.Inferno,
                                      text = 'sales')
        fig_sales_product.update_traces(marker_line_width = 0, texttemplate='%{y}', hovertemplate =  df_top_product['product_name'])
        fig_sales_product.update_layout(
                title = 'Sales Based on Product',
                xaxis = dict(
                    title = 'Product Name',
                    tickangle = 90,
                    tickfont = dict(size = 12),
                    rangeslider = dict(visible = True)),
                    yaxis = dict(title='Sales'),
                    width = 1200,
                    height = 500,
                    margin = dict(l = 40, r = 40, t = 40, b = 40))
        st.plotly_chart(fig_sales_product)

        
    revenue_top_products, pct_contribute = st.columns(2)
    with revenue_top_products:
        df_rev_products = filtered_df.groupby('short_name').agg(
                {   'product_name':'min',
                    'revenue':'sum'}).reset_index()
            
        fig_rev_product = px.bar(df_rev_products, x = 'short_name', y='revenue',color = 'revenue',labels ='Product Name',
                                     color_continuous_scale = px.colors.sequential.Viridis,text = 'revenue')
        fig_rev_product.update_traces(marker_line_width=0,texttemplate = "%{y}", hovertemplate = df_rev_products['product_name'])
        fig_rev_product.update_layout(
                title = 'Revenue Based on Products(Rp)',
                xaxis = dict(
                    title = 'Product Name',
                    tickangle = 90,
                    tickfont = dict(size = 12),
                    rangeslider=dict(visible=True)),
                    yaxis = dict(title ='Revenue(Rp)'),
                    width = 500,
                    height = 500,
                    margin = dict(l=40,r=40,t=40,b=40),
            )
        st.plotly_chart(fig_rev_product)
    
    with pct_contribute:
        filtered_df['short_name'] = filtered_df['product_name'].apply(lambda x:shorten_name(x,20))
        pct_contribute_df = filtered_df.groupby('short_name').agg({
            'product_name':'max',
            'revenue':'sum',           
        }).reset_index()

        pct_contribute_df = calculate_pct_revenue(pct_contribute_df)

        fig_pct_contribute = px.pie(pct_contribute_df, values = 'pct_revenue', 
                                    names = 'short_name',
                                    hover_data = ({'product_name':True}))

        fig_pct_contribute.update_traces(marker_line_width=0)
        fig_pct_contribute.update_layout(
                title = 'Each Product Contribution to Company Revenue  ',
                xaxis = dict(
                    title = 'Product Name',
                    tickangle = 90,
                    tickfont = dict(size = 12),
                    rangeslider=dict(visible=True)),
                    yaxis = dict(title ='Revenue Percentage Contribution(Rp)'),
                    width = 450,
                    height = 450,
                    margin = dict(l=40,r=40,t=40,b=40))
                    
        st.plotly_chart(fig_pct_contribute)
             

            
            












































if __name__ == "__main__":
    main()
