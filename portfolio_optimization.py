import streamlit as st
from vnquant import DataLoader
import pandas as pd
import numpy as np
from tqdm import tqdm
import plotly.graph_objects as go



# TODO: Change values below and observer the changes in your app
# st.markdown(
#         f"""
# <style>
#     .reportview-container .main .block-container{{
#         max-width: 90%;
#         padding-top: 5rem;
#         padding-right: 5rem;
#         padding-left: 5rem;
#         padding-bottom: 5rem;
#     }}
#     img{{
#     	max-width:40%;
#     	margin-bottom:40px;
#     }}
# </style>
# """,
#         unsafe_allow_html=True,
#     )
#######################################


# here is how to create containers
header_container = st.beta_container()
stats_container = st.beta_container()	
#######################################



# You can place things (titles, images, text, plots, dataframes, columns etc.) inside a container
with header_container:

	# for example a logo or a image that looks like a website header
	st.image('imags/logo.png')

	# different levels of text you can include in your app
	st.title("Investment Portfolio Optimisation With Python")
	st.header("Welcome!")
	st.write('......................................................................')
	st.subheader('Take a look with your stocks')

st.header("Let's pick your date")
start = str(st.date_input('Start date')) # Pick start date
end = str(st.date_input('End date')) # Pick end date

def load_data(tickers, start, end):
	data_load_state = st.text('Loading data...')
	loader = DataLoader.DataLoader(tickers, start, end, minimal=True) # Load dữ liệu từ VnDirect
	df = loader.download()['close'] # Chỉ lấy giá đóng cửa của các mã cổ phiếu.
	df.dropna(inplace=True) # Các ngày không có giao dịch sẽ chưa các giá trị NaN -> loại bỏ
	data_load_state.text('Loading data...done!')
	return df


# Plot line chart with tickets



try:
	s_stock = st.text_input(label="Type your stock")
	# display the collected input
	st.write('You selected the stock: ' + str(s_stock))
	data_load_state = st.text('Loading data...')
	loader = DataLoader.DataLoader([s_stock], start, end, minimal=True)
	df = loader.download()
	df.columns = ['High', 'Low', 'Open', 'Close', 'Adjust', 'Volume']
	df = df.reset_index()
	df = df.dropna()
	# Các ngày không có giao dịch sẽ chưa các giá trị NaN -> loại bỏ
	data_load_state.text('Loading data...done!')


	fig = go.Figure(data=go.Ohlc(x=df['date'],
						open=df['Open'].values,
						high=df['High'].values,
						low=df['Low'].values,
						close=df['Close'].values))

	fig.update_layout(title="BVH")
	fig.update_layout(autosize=False,
					width=900,
					height=500)
	#                   margin=dict(l=50,r=50,b=100,t=100,pad=4),
	#                   paper_bgcolor="LightSteelBlue")


	st.write(fig)

except:
	st.write("You don't have stock yet")




st.subheader("Let's build your portfolio")
try:
	str_input = st.text_input(label="Type your tickers")
	tickers = str_input.strip().split()	
	# display the collected input
	st.write('You choose tickers: ', tickers)
	df = load_data(tickers, start, end)
	# # Plot line chart
	# st.line_chart(df[s_stock])
except:
	st.write("You haven't portfolio yet!!!")


def optimal_portfolio(df):
# thay đổi giá đóng cửa hàng ngày (đơn vị %)

	cov_matrix = df.pct_change().apply(lambda x: np.log(1+x)).cov()

	# Lợi nhuận kỳ vọng hàng năm
	ind_er = df.resample('Y').last().pct_change().mean()

	pf_return = []
	pf_std = []
	pf_weights = []

	num_assets = len(df.columns) # = 5
	num_portfolios = 10000 # Giả lập 100,000 danh mục dổ phiếu


	for i in tqdm(range(num_portfolios)):
		weights = np.random.random(num_assets) # chạy random từ 1 -> 5
		weights = weights/np.sum(weights)
		pf_weights.append(weights)
		returns = np.dot(weights, ind_er)
		pf_return.append(returns)
		std = np.sqrt(cov_matrix.mul(weights, axis=0).mul(weights, axis=1).sum().sum()) 
		pf_std.append(std)



	data = {'Returns':pf_return, 'Standard_Deviation':pf_std}

	for counter, symbol in enumerate(df.columns.tolist()):
		data[symbol+' weight'] = [w[counter] for w in pf_weights]
    
	portfolios  = pd.DataFrame(data)

	risk_free = 0.01 # rủi ro thị trường là 10%
	portfolios['Sharpe_ratio'] = ((portfolios['Returns'] - risk_free)/portfolios['Standard_Deviation'])

	# # Danh mục đầu tư có độ lệch chuẩn thấp nhất
	# min_std_port = portfolios.iloc[portfolios['Standard_Deviation'].idxmin()]  

	return portfolios

	
try:
	portfolios = optimal_portfolio(df)
	min_std_port = portfolios.iloc[portfolios['Standard_Deviation'].idxmin()]
	optimal_port = portfolios.iloc[portfolios['Sharpe_ratio'].idxmax()]  


	fig = go.Figure()

	#min_std_port[1], min_std_port[0]
	# Add traces
	fig.add_trace(go.Scatter(x=portfolios['Standard_Deviation'], y=portfolios['Returns'],
						mode='markers',
						name='Portfolios'))
	fig.add_trace(go.Scatter(x=[min_std_port['Standard_Deviation']], y=[min_std_port['Returns']],
						mode='markers',
						name='Minimum Standard Deviation', marker=dict(color='Red',size=12)))
	fig.add_trace(go.Scatter(x=[optimal_port['Standard_Deviation']], y=[optimal_port['Returns']],
						mode='markers',
						name='Maximum Sharpe Ratio', marker=dict(color='LightSkyBlue',size=12)))

	fig.update_layout(autosize=False,
					width=900,
					height=600)
	#                   margin=dict(l=50,r=50,b=100,t=100,pad=4),
	#                   paper_bgcolor="LightSteelBlue")

	fig.update_layout(title="All Portfolios", 
					xaxis_title="Standard Deviation", 
					yaxis_title="Returns") 
	#                   legend_title="Legend Title",
	#                   font=dict(family="Courier New, monospace",
	#                             size=18,
	#                             color="RebeccaPurple"))

	st.write(fig)

	st.write("Here are your portfolios: ")
	min_std = portfolios[portfolios['Standard_Deviation'] == min(portfolios['Standard_Deviation'])]
	max_sharpe = portfolios[portfolios['Sharpe_ratio'] == max(portfolios['Sharpe_ratio'])]
	result = pd.concat([min_std, max_sharpe])

	result.index = ['Minimum Satandard Deviation', 'Maximum Shapre Ratio']

	st.write(result)

except:
	st.write("You haven't portfolio yet!!!")

