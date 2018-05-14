'''
    Using Python Dash framework
    Container stat visualization in browser
'''
import dash
from dash.dependencies import Output,Input,Event,State
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from mongoGuest import mongoGuest
from dockerGuest import dockerGuest
import random
docker=dockerGuest()
mongo = mongoGuest()
app = dash.Dash(__name__)

#---------------CSS Styling------------#

table_style = {
    'borderCollapse':'collapse',
    'width':'100%',
    'fontSize':'14px'
    
    }
tableh_style = {
    'border':'1px solid #dddddd',
    'padding':'8px',
    'backgroundColor':'#F2F2F2',
    }
tabled_style = {
    'border':'1px solid #dddddd',
    'padding':'8px',
    }

#-------------------------------------#
#image_list=docker.get_cont_list()

#------------APP Layout-------------------------------------------#
def generate_table():
    return html.Table(
      [html.Tr([html.Th('Name'),html.Th('IPAddress'),html.Th('Image')],style=tableh_style)]+
[html.Tr([dcc.Link(html.Td(con['name']),href=con['name']),html.Td(con['IPAddress']),html.Td(con['Image'])],
         style=tabled_style) for con in docker.get_cont_list()],className='table table-bordered',style=table_style     
    )

def serve_layout():
    return html.Div([
        dcc.Location(id='url',refresh=True),
        html.Div(id='page-content')
        ],className='container')


    
index_page=html.Div([
        html.Div([
            html.Div([
            html.H2('Cisco Anagram-Analytics',style={'color':'#FFFFFF'})]
                     ,className='col-md-10',style={'textAlign':'left'}),
            html.Div([
                html.Button(id='gen-table',n_clicks=0,children='Refresh',className='btn btn-primary'),
                ],className='col-md-2')
           ],className='row',style={'textAlign':'center','backgroundColor':'#009edf'}),
        html.Div([
               html.Div([
                   
                   ],id='table'),
            ],className='row'),
        ],id='index-page' )

graph_page=html.Div([
             html.Div([
                 dcc.Dropdown(
                     id='usage',
                     options=[{'label':'CPU ns','value':'cpu_usage'},{'label':'Memory','value':'mem_usage'},
                              {'label':'CPU %','value':'cpupercent_usage'}],
                     value='cpupercent_usage',
                     ),
                 html.Div([dcc.Link('Go back to list',href='/'),],style={'paddingTop':'20px','float':'left'}),
                 ],className='row',style={'textAlign':'center'}),

              html.Div([
                  html.H4([
                      'Name: ',html.Span(id='cont-name'),]),
                  ],className='row',style={'textAlign':'left'}),

              html.Div([
                  html.H4([
                      'IPAddress: ',html.Span(id='cont-ip'),]),
                  ],className='row',style={'textAlign':'left'}),
                
              html.Div([
                  dcc.Graph(id='usage-graph'),
                  
                  dcc.Slider(
                      id='intervals',
                      min=1,
                      max=10,
                      value=10,
                      marks={i:str(i) for i in range(1,10)}
                      ),
                  
                  ],className='row'),
               
              html.Div([
                  html.Div([
                      html.H3([
                          'Max Usage: ',
                          html.Span(id='max-usage'),
                          ]),
                      html.H3([
                          'Min Usage: ',
                          html.Span(id='min-usage'),
                          ]),
                
                      ],className='col-md-6')
                  ],className='row'),
    
            ],id='graph-page')
            
    

app.layout = serve_layout
app.config['suppress_callback_exceptions']=True
#------------Event Handlers---------------------------#

'''navigation of pages'''
@app.callback(Output('page-content','children'),
              [Input('url','pathname')])
def render(pathname):
    if pathname == '/':
        return index_page
    else:
        return graph_page

'''
     generate container list table in target host
'''
@app.callback(Output('table','children'),
              [Input('gen-table','n_clicks')])
def show_table(n_clicks):
    if n_clicks>=0:
        return generate_table()

@app.callback(Output('cont-name','children'),
              [Input('usage','value'),Input('url','pathname')])
def show_name(value,pathname):
    return pathname[1:]

@app.callback(Output('cont-ip','children'),
              [Input('usage','value'),Input('url','pathname')])
def show_ip(value,pathname):
    return docker.get_ip(pathname[1:])

#------ Usage Graph generating callback-----------------#

def generate_cpu_data(cont_id,percent=False):
    return mongo.get_cpu_usage(cont_id,percent)

def generate_memory_data(cont_id):
    return mongo.get_memory_usage(cont_id)

'''
    Event handler to generate graph
'''
@app.callback(Output('usage-graph','figure'),
              [Input('usage','value'),Input('url','pathname'),
               ])
def show_cpu_usage_graph(value,pathname):#,slider_value):
    usage = ''
    if value == 'mem_usage':
        X,Y = generate_memory_data(pathname[1:])
        usage = 'Memory(bytes)'
    elif value=='cpu_usage':
        X,Y = generate_cpu_data(pathname[1:])
        usage = 'CPU ns'
    elif value =='cpupercent_usage':
        X,Y = generate_cpu_data(pathname[1:],percent=True)
        usage = 'CPU %'
    #print(slider_value)
    #start = 6*(slider_value-1)
    #X=X[start:start+6]
    #Y=Y[start:start+6]
    if len(X) >0:
        mins = X[-1]
        #mins=''
    data = go.Scatter(
            x = X,
            y = Y,
            name='Scatter',
            mode='none',
            fill='tonexty',
            )
    if len(X) > 0:
        layout = go.Layout(
            xaxis={'title':'Time('+'last '+str(mins)+' mins)','range':[min(X),max(X)]},
            yaxis={'title':usage,'range':[min(Y),max(Y)]},
            )
    else:
        layout =go.Layout(
            xaxis = {'title':'Time'},
            yaxis = {'title':usage},
            margin={'l':40,'b':40,'t':10,'r':10},
        
            )
    return {'data':[data],'layout':layout}

@app.callback(Output('max-usage','children'),
              [Input('usage','value'),Input('url','pathname')])
def max_usage(value,pathname):
    if value == 'mem_usage':
        _,Y = generate_memory_data(pathname[1:])
    elif value=='cpu_usage':
        _,Y = generate_cpu_data(pathname[1:])
    else:
        _,Y = generate_cpu_data(pathname[1:],percent=True)
    if len(Y) > 0:
        return max(Y)
@app.callback(Output('min-usage','children'),
              [Input('usage','value'),Input('url','pathname')])
def min_usage(value,pathname):
    if value ==' mem_usage':
        _,Y = generate_memory_data(pathname[1:])
    elif value == 'cpu_usage':
        _,Y = generate_cpu_data(pathname[1:])
    else:
        _,Y = generate_cpu_data(pathname[1:],percent=True)
    if len(Y)>0:
        return min(Y)
@app.callback(Output('cpu-usage-title','children'),
              [Input('usage','value')])
def show_title(value):
    if value=='memory_usage':
        return ' bytes'
    elif value =='cpu_usage':
        return ' %'
    else:
        return ' nanoseconds'
#----------------------------------------------
#---------------------------------------------



#---------------Bootstrap CSS-------------------#

''' Bootstrap using CDN. This will be changed later. Normal CSS will be used'''

my_css_url = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
app.css.append_css({
    "external_url":my_css_url
    })

#------------------------------------------------#

'''Running the dash app'''
if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0',port=8080)

