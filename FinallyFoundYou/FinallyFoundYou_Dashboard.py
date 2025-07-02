import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import os
import regex

def main():
    st.set_page_config(
        page_title = 'Finally Found You Product Dashboard 2025',
        layout = 'wide',
        initial_sidebar_state = 'expanded')

    st.title('Finally Found You Product Dashboard 2025')

    #Loading the Dataset
    @st.cache_data
    def load_data(url):
        df = pd.read_csv(url)
        return df
    
    df = load_data('CleanData_FinallyFoundYou_30625.csv')

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

    with st.sidebar:
        st.title('"Finally Found You" Moisturizer Products')

        #create month_list for the filter
        df['month'] = df['month'].map(month_order)
        month_list = df['month'].unique().tolist()
        category_list = df['categories'].unique().tolist()
        
        #button mechanisms
        selected_month = st.selectbox('Select a month', month_list, index = len(month_list)-1)
        selected_categories = st.selectbox('Select a Category', category_list,index = len(category_list)-1)
        df_selected_month = df[(df['month'] == selected_month) & (df['categories'] == selected_categories)]

        def calculate_revenue_metric(month,category):
            revenue_total = df_selected_month['revenue'].sum()
            return revenue_total
        
        def calculate_sales_metric(month,category):
            sales_total = df_selected_month['sales'].sum()
            return sales_total
        
        def calculate_product_rating(month,category):
            rating_mean = df_selected_month['rating'].mean()
            return rating_mean
       
        def calculate_pct_revenue(df):                        # hindari SettingWithCopy
            df_selected_month['revenue'] = pd.to_numeric(df_selected_month['revenue'], errors='coerce')

            total = df_selected_month['revenue'].sum()

            if total == 0:
                df_selected_month['pct_revenue'] = 0.0
            else:
                df_selected_month['pct_revenue'] = (100*df_selected_month['revenue'] / total ).round(2)
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
        
    total_rev, total_sales,avg_rating = st.columns(3)
    st.markdown("""<style>
        [data-testid="stMetricValue"] {
        font-size: 60px;
        }
        </style>
        """, unsafe_allow_html=True)
    df_selected_month['short_name'] = df_selected_month['product_name'].apply(lambda x:shorten_name(x,20))
    with total_rev:
            total_rev = calculate_revenue_metric(selected_month,selected_categories)
            st.metric(label = f'Revenue in {selected_month} 2025', value = f'{format_number(total_rev)} Rupiah')
    with total_sales:
            total_sales = calculate_sales_metric(selected_month,selected_categories)
            st.metric(label = f'Sales  in {selected_month} 2025',value = f'{format_number(total_sales)} units')
    with avg_rating:
            avg_rating = calculate_product_rating(selected_month,selected_categories)
            st.metric(f'Rating of  in {selected_month} 2025', value = round(avg_rating,2))    

    sales_histogram = st.columns(1)[0]
    with sales_histogram:
        df_sales_hist = df_selected_month.groupby('Price Range').agg(
            {
                'sales':'sum'
            }
        ).reset_index().sort_values(by = 'Price Range')
        
        fig_hist = px.bar(df_sales_hist, x = 'Price Range', y = 'sales', color = 'Price Range',
                        color_discrete_sequence = px.colors.sequential.Plasma_r, text = 'Price Range')
        fig_hist.update_traces(marker_line_width = 1, texttemplate = "%{y}") 
        fig_hist.update_layout(
            title = 'Sales per Price Range',
            xaxis = dict(
                title = 'Price Range(Rp)',
                tickangle = 45,
                tickfont = dict(size = 10),
                rangeslider = dict(visible = False)
            ),
            yaxis = dict(title = 'Total Product Sold'),
            width  =500,
            height = 500,
            margin = dict(
                l = 40,
                r = 40,
                t = 40,
                b = 40)
        )
        fig_hist.update_layout(bargap = 0.1)
        st.plotly_chart(fig_hist, use_container_width = True)
        
        #revenue based on product, sales based on product, contribution of each product revenue to whole company revenue
    product_list = df_selected_month['product_name'].unique().tolist()

    #filtered_df_1 = df_selected_month['product_name'==product_name_1]
    #filtered_df_2 = df_selected_month['product_name' == product_name_2]

    product_compare_timeline = st.columns(1)[0]
    button1, button2 = st.columns(2) 
    with product_compare_timeline:
        with button1:
            prod_a= st.selectbox('Choose a Product to Compare', product_list, index = len(product_list)-1)
            metric = st.radio('Choose a metric', options =['sales','revenue'],horizontal=True)
        with button2:
            prod_b = st.selectbox('Choose other Product to Compare',product_list, index=len(product_list)-1)
        #create a df that only take categories of product
        df_categories = df[(df['categories'] == selected_categories) & df['product_name'].isin([prod_a,prod_b])]

        fig_timeline = px.line(
              df_categories,
              x='scraping_date',
              y=metric,
              color =  'product_name',
              color_discrete_sequence = px.colors.sequential.Inferno,
              markers = True,
              title = f'{metric.capitalize()} of {prod_a} vs {prod_b} in 2025',
              labels = {'scraping_date':'Date', metric:metric.capitalize()}
         )
        
        fig_timeline.update_layout(hovermode='x unified')
        st.plotly_chart(fig_timeline, use_container_width=True)
        
    rev_product, sales_product, contrib_rev = st.columns(3)

    with rev_product:
            df_rev_product = df_selected_month.groupby('short_name').agg(
                  {
                       'product_name':'min',
                       'revenue':'sum'
                  }
             ).reset_index().sort_values(by='revenue', ascending = False)

            fig_rev = px.bar(df_rev_product, x = 'short_name', 
                             y = 'revenue',
                             hover_data = {"product_name":True},
                             color = 'revenue',
                             labels = {"short_name":"Produk",
                                       'revenue':'Revenue(Rp)'},
                             color_continuous_scale = px.colors.sequential.Viridis, 
                             text = 'revenue')
            
            fig_rev.update_traces(marker_line_width = 0, 
                                  texttemplate = "%{y}", hovertemplate = 
                                  '<br>%{customdata[0]}<br>' +
                                  '%{y} Rupiah<br>')
            
            fig_rev.update_layout(
                 title = 'Revenue Based on Products(Rp)',
                 xaxis = dict(
                      title = 'Product Name',
                      tickangle = 90,
                      tickfont = dict(size = 10),
                      rangeslider = dict(visible = True)),
                      yaxis = dict(title='Revenue(Rp)'),
                      width = 500,
                      height = 500,
                      margin = dict(
                           l = 40,
                           r = 40,
                           b = 40,
                           t = 40
                      )
                 )
            

            st.plotly_chart(fig_rev)
    with sales_product:
        df_sales_product = df_selected_month.groupby('short_name').agg({
                 'product_name':'min',
                 'sales':'sum'
            }).reset_index()
        
        fig_sales_product = px.bar(df_sales_product, x= 'short_name', y = 'sales',
                                       hover_data = {'product_name':True},
                                       color = 'sales',
                                       labels = {"short_name":"Product Name","sales":"Sales"},
                                       color_continuous_scale = px.colors.sequential.Turbo,
                                       text = 'sales')
        fig_sales_product.update_traces(marker_line_width = 0, texttemplate="%{y}",
                                            hovertemplate = '<br>%{customdata[0]}<br>' + '%{y} units<br>')
            
        fig_sales_product.update_layout(
                 title = 'Sales Based on Product in {selected_month} 2025',
                 xaxis = dict(
                      title = 'Product Name',
                      tickangle = 90,
                      tickfont = dict(size = 10),
                      rangeslider = dict(visible = True)),
                      yaxis = dict(title='Sales'),
                      width = 500,
                      height = 500,
                      margin = dict(
                           l = 40,
                           r = 40,
                           b = 40,
                           t = 40
                      )
                 )
            
        st.plotly_chart(fig_sales_product)


        with contrib_rev:   
            pct_contribute_df = calculate_pct_revenue(df_selected_month)

            fig_pct_contribute = px.pie(pct_contribute_df, values = 'pct_revenue',
                                             names = 'short_name',
                                             hover_data = ({
                                                  'product_name':True
                                             }))
            fig_pct_contribute.update_traces(marker_line_width = 0)
            fig_pct_contribute.update_layout(
                     title = 'Each Product Contribution to Company''s Revenue',
                     xaxis = dict(
                          title = 'Product Name',
                          tickangle = 90,
                          tickfont = dict(size=12),
                          rangeslider = dict(visible =True)),
                          yaxis = dict(title = 'Revenue Percentage(%)'),
                          width = 450,
                          height = 450,
                          margin = dict(
                               l = 40,
                               r = 40,
                               t = 40,
                               b = 40
                          ))

            st.plotly_chart(fig_pct_contribute)




























if __name__ == "__main__":
    main()

