/**
 * In this file, we create a React component
 * which incorporates components provided by Material-UI.
 */
import React, {Component} from 'react';
import cookie from 'cookie';

import Dialog from 'material-ui/Dialog';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import TextField from 'material-ui/TextField';
import Snackbar from 'material-ui/Snackbar';

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
      filename: '',
      body: false,
      response: false,
      token: location.search.substr(1).split("=")[1],
      isPublic: false,
      ...cookie.parse(document.cookie)
    }

    window.onpopstate = e => {
      if(e.state && e.state.folder) this.list(e.state.folder)
    }
  }

  setPublic = (state) => {
    this.setState({
      isPublic: state
    })
  }

  
  uploadClose = () => {
    this.setState({
      open: false,
      body: false,
      fileName: false,
    })
  }
  
  uploadClick = () => {
    this.setState({
      open: true,
    })
  }

  doSetPublicTag = (name, state) => {
    const { folder } = this.state
    fetch(`${name}?public=${state === true ? "False" : "True"}`, {
      method: "PUT",
    })
    .then(response => response.text())
    .then(text => {
      this.setState({ response: text })
      this.list(folder)
    })
  }
  
  doUpload = () => {
    const { file, folder, body, isPublic } = this.state
    if(file) {
      fetch(`${file}?public=${isPublic ? "True" : "False"}`, {
          method: 'POST',
          body: body,
        })
        .then(response => response.text())
        .then(text => {
          this.setState({response: text, open: false, filename: false})
          this.list(folder)
        })
    }
  }

  onDelete = res => {
    res.text().then(text => {
      this.setState({response: text})
      this.list(this.state.folder)
    })
  }

  textChange = e => {
    this.setState({file: e.target.value})
  }

  fileChange = e => {
    const files = e.target.files || e.dataTransfer.files

    if(!files.length) return

    const file = files[0]
    const body = new FormData()
    const name = file.name

    body.append('file', file)
    body.append('token', this.state.token)

    this.setState({body, filename: name})
  }

  parrentFolder = e => {
    e.preventDefault()
    const {folder} = this.state
    const parrent = folder.split('/').slice(0, -2).join('/')
    this.changeFolder(`${parrent}/`)
  }

  changeFolder = folder => {
    fetch(`${folder}?list`)
      .then(res => res.json())
      .then(res => {
        this.setState({folder, ...res})
        history.pushState({folder}, `Yoggi - ${folder}`, folder);
      })
  }

  list = folder => {
    return fetch(`${folder}?list`)
      .then(res => res.json())
      .then(res => {
        this.setState({folder, ...res})
      })
  }

  componentDidMount() {
    this.changeFolder(this.state.folder)
  }

  render() {
    const {files, folders, folder, token, tags} = this.state
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
              filename={this.state.filename}
              permissions={this.state.permissions}
              uploadClose={this.uploadClose}
              doUpload={this.doUpload}
              fileChange={this.fileChange}
              textChange={this.textChange}
              setPublic={this.setPublic}
              isPublic={this.state.isPublic}
            />

            <Browser
              files={files.filter(file => `/${file}` != folder)}
              tags={tags}
              folders={folders}
              folder={folder}
              token={token}
              changeFolder={this.changeFolder}
              onDelete={this.onDelete}
              onPublicSet={this.doSetPublicTag}
            />

          </div>
          <Snackbar
            open={this.state.response}
            message={this.state.response}
            autoHideDuration={4000}
            onRequestClose={() => this.setState({response: false})}
          />
        </div>
      </MuiThemeProvider>
    )
  }
}

function Upload(props) {
  const {open, filename, permissions} = props
  const {uploadClose, doUpload, fileChange, textChange, setPublic, isPublic} = props
  return (<Dialog
    open={open}
    title="Upload a file"
    actions={[
      <FlatButton label="Cancel" onTouchTap={uploadClose} />,
      <RaisedButton label="Upload" primary={true} onTouchTap={doUpload} />,
    ]}
    onRequestClose={uploadClose}>
    <p>
      Everyone is allowed to upload to the root directory.
      { permissions.length ? <span>
        <br />
        You also have permissions for the following folders: { permissions }
      </span> : null}
    </p>
    <TextField
      inputStyle={{
        textAlign: 'center',
      }}
      autoFocus
      fullWidth={true}
      hintText="Desired filename (including folder)"
      hintStyle={{
        textAlign: 'center',
        width: '100%',
      }}
      onChange={textChange}
    />
    <RaisedButton
      fullWidth={true}
      containerElement='label'
      label={filename || 'Select file'}
    >
      <input
        type="file"
        style={{display: 'none'}}
        onChange={fileChange}
      />
    </RaisedButton>
    <RaisedButton
      fullWidth={true}
      primary={isPublic}
      containerElement='label'
      label={'Ladda upp som publik: ' + (isPublic ? "Ja" : "Nej")}
      onClick={() => setPublic(isPublic === true ? false : true)}
      title="Publika filer kan nås av vem som helst på internet"
    >
    </RaisedButton>
  </Dialog>)
}

export default Main
