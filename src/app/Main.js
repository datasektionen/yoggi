/**
 * In this file, we create a React component
 * which incorporates components provided by Material-UI.
 */
import React, {Component} from 'react';

import Dialog from 'material-ui/Dialog';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import TextField from 'material-ui/TextField';

import getMuiTheme from 'material-ui/styles/getMuiTheme';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import {deepOrange400, deepOrange500} from 'material-ui/styles/colors';

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
      folder: window.location.pathname,
      folders: [],
      files: [],
      file: '',
      body: false,
      token: location.search.substr(1).split("=")[1]
    }

    window.onpopstate = e => this.changeFolder(e.state.folder)
  }

  uploadClose = () => {
    this.setState({
      open: false
    })
  }

  uploadClick = () => {
    this.setState({
      open: true
    })
  }

  doUpload = () => {
    const {file, folder, body} = this.state
    if(file) {
      fetch(file, {
          method: 'POST',
          body: body
        }).then(response => response.text())
          .then(text => {
            this.setState({response: text, open: false})
            this.list(folder, 'files')
          })
    }
  }

  onDelete = () => {
    this.list(this.state.folder, 'files')
  }

  textChange = e => {
    this.setState({file: e.target.value})
  }

  fileChange = e => {
    const files = e.target.files || e.dataTransfer.files

    if(!files.length) return

    const file = files[0]
    const body = new FormData()

    body.append('file', file)
    body.append('token', this.state.token)

    this.setState({body})
  }

  parrentFolder = e => {
    e.preventDefault()
    const {folder} = this.state
    const parrent = folder.split('/').slice(0, -2).join('/')
    this.changeFolder(parrent + '/')
  }

  changeFolder = folder => {
    fetch(folder + '?list')
      .then(res => res.json())
      .then(res => {
        this.setState({folder, ...res})
        history.pushState({folder}, `Yoggi - ${folder}`, folder);
      })
  }

  list = (folder, type) => {
    return fetch(folder + '?list=' + type)
      .then(res => res.json())
      .then(res => {
        this.setState({[type]: res})
      })
  }

  componentDidMount() {
    this.changeFolder(this.state.folder)
  }

  render() {
    const {files, folders, folder, token} = this.state
    return (
      <MuiThemeProvider muiTheme={muiTheme}>
        <div>
          <header>
            <div className="header-inner">
              <div className="row">
                <div className="header-left col-md-2">
                  <a href="../" onTouchTap={this.parrentFolder}>« Back</a>
                </div>
                <div className="col-md-8">
                  <h2>Yoggi</h2>
                </div>
                <div className="header-right col-md-2">
                  <a href="#" className="primary-action" onTouchTap={this.uploadClick}>Upload</a>
                </div>
              </div>
            </div>
          </header>
          <div id="content">
            <Upload
              open={this.state.open}
              uploadClose={this.uploadClose}
              doUpload={this.doUpload}
              fileChange={this.fileChange}
              textChange={this.textChange}
            />

            <Browser 
              files={files.filter(file => '/' + file != folder)}
              folders={folders}
              folder={folder}
              token={token}
              list={this.list}
              changeFolder={this.changeFolder}
              onDelete={this.onDelete}
            />

          </div>
        </div>
      </MuiThemeProvider>
    )
  }
}

function Upload(props) {
  const {open, uploadClose, doUpload, fileChange, textChange} = props
  return (<Dialog
    open={open}
    title="Upload a file"
    actions={[<FlatButton label="Cancel" onTouchTap={uploadClose} />,
              <RaisedButton label="Upload" primary={true} onTouchTap={doUpload} />]}
    onRequestClose={uploadClose}>
    <TextField
      autoFocus
      fullWidth={true}
      hintText="Desired filename (including folder)"
      onChange={textChange}
    />
    <RaisedButton
      fullWidth={true}
      containerElement='label'
      label='Select file'>
        <input 
          type="file"
          style={{display: 'none'}}
          onChange={fileChange}
        />
    </RaisedButton>
  </Dialog>)
}

export default Main
