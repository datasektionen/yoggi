/**
 * In this file, we create a React component
 * which incorporates components provided by Material-UI.
 */
import React, {Component} from 'react';
import {deepOrange400, deepOrange500} from 'material-ui/styles/colors';

import {List, ListItem} from 'material-ui/List';
import Subheader from 'material-ui/Subheader';
import Divider from 'material-ui/Divider';

import IconButton from 'material-ui/IconButton'
import ActionDelete from 'material-ui/svg-icons/action/delete'

const apiUrl = 'http://localhost:5000/'

class Browser extends Component {
  constructor(props, context) {
    super(props, context)

    this.state = {
      path: '',
      files: [],
      folders: []
    }

    this.componentDidMount = this.componentDidMount.bind(this)
    this.changePath = this.changePath.bind(this)
    this.list = this.list.bind(this)
  }

  componentDidMount() {
    this.changePath('')
  }

  changePath(path) {
    this.list(path, 'files')
    this.list(path, 'folders')
    this.setState({path})
  }

  list(path, type) {
    return fetch(apiUrl + path + '?list=' + type)
      .then(res => res.json())
      .then(res => {
        this.setState({[type]: res})
      })
  }

  render() {
    const {path, files, folders} = this.state
    return (<div>
      <h1>path: { path } </h1>
      <Divider />
      <Subheader>Folders</Subheader>
      <List>
        {folders.map(folder => <FolderItem
          key={folder}
          name={folder}
          changePath={this.changePath} />)}
      </List>
      <Divider />
      <Subheader>Files</Subheader>
      <List>
        {files.map(file => <FileItem
          key={file}
          name={file} />)}
      </List>
    </div>)
  }
}

function FolderItem(props) {
  const {name, changePath} = props

  return (
    <ListItem 
      primaryText={name}
      onClick={() => changePath(name)} />
  )
}

function FileItem(props) {
  const {name} = props

  const deleteFile = () => {
    fetch(apiUrl + name, {method: 'DELETE'}).then(res => console.log(res))
  }

  return (
    <ListItem 
      primaryText={name}
      onClick={() => location.href = apiUrl + name}
      rightIconButton={<IconButton onClick={deleteFile}><ActionDelete /></IconButton>} />
  )
}

export default Browser
