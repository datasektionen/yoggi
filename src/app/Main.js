/**
 * In this file, we create a React component
 * which incorporates components provided by Material-UI.
 */
import React, {Component} from 'react';
import RaisedButton from 'material-ui/RaisedButton';
import Dialog from 'material-ui/Dialog';
import {deepOrange400, deepOrange500} from 'material-ui/styles/colors';
import FlatButton from 'material-ui/FlatButton';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';

import Browser from './Browser'

const styles = {
  container: {
    textAlign: 'center',
    paddingTop: 200,
  },
}

const muiTheme = getMuiTheme({
  palette: {
    primary1Color: deepOrange400,
    accent1Color: deepOrange500,
  },
})

class Main extends Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      open: false,
    }
  }

  uploadClose = () => {
    this.setState({
      open: false
    })
  }

  uploadTap = () => {
    this.setState({
      open: true
    })
  }

  render() {
    return (
      <MuiThemeProvider muiTheme={muiTheme}>
        <div>
          <header>
            <div className="header-inner">
              <div className="row">
                <div className="header-left col-md-2">
                </div>
                <div className="col-md-8">
                  <h2>Yoggi</h2>
                </div>
                <div className="header-right col-md-2">
                  <RaisedButton
                    label="Upload"
                    primary={true}
                    onTouchTap={this.uploadTap}
                  />
                </div>
              </div>
            </div>
          </header>
          <div id="content">
            <Dialog
              open={this.state.open}
              title="Super Secret Password"
              actions={[
                <FlatButton label="Cancel" primary={true} onTouchTap={this.uploadClose} />,
                <FlatButton label="Upload" primary={true} onTouchTap={this.doUpload} />]}
              onRequestClose={this.uploadClose}
            >
              <RaisedButton
                containerElement='label'
                label='Select file'>
                  <input type="file" />
              </RaisedButton>
            </Dialog>

            <Browser />

          </div>
        </div>
      </MuiThemeProvider>
    );
  }
}

export default Main
