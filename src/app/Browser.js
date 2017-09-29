/**
 * In this file, we create a React component
 * which incorporates components provided by Material-UI.
 */
import React, {Component} from 'react';
import {deepOrange400, deepOrange500} from 'material-ui/styles/colors';

import {List, ListItem} from 'material-ui/List';
import RaisedButton from 'material-ui/RaisedButton';
import Subheader from 'material-ui/Subheader';
import Divider from 'material-ui/Divider';

import IconButton from 'material-ui/IconButton'
import ActionDelete from 'material-ui/svg-icons/action/delete'

function Browser(props) {
  const {folder, files, folders, token, changeFolder, onDelete} = props

  return (<div>
    <Subheader>{folder}</Subheader>
    <Subheader>Folders</Subheader>
    <List>
      {folders.map(folder => <FolderItem
        key={folder}
        name={folder}
        changeFolder={changeFolder} />)}
    </List>
    <Divider />
    <Subheader>Files</Subheader>
    <List>
      {files.map(file => <FileItem
                            key={file}
                            name={file}
                            token={token}
                            onDelete={onDelete}
                          />)}
    </List>
  </div>)
}

function FolderItem(props) {
  const {name, changeFolder} = props

  return (
    <ListItem
      primaryText={name}
      onTouchTap={() => changeFolder(`/${name}`)} />
  )
}

function FileItem(props) {
  const {name, onDelete} = props

  const deleteFile = e => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm(`Delete ${name}?`)) fetch(`/${name}?token=${props.token}`, {method: 'DELETE'}).then(onDelete)
  }

  const deleteButton = (
    <IconButton
      style={{boxShadow: 'none'}}
      hoveredStyle={{boxShadow: 'none'}}
      onClick={deleteFile}>
      <ActionDelete />
    </IconButton>
  )

  return (
    <a href={`/${name}`}> <ListItem 
      primaryText={name}
      rightIconButton={deleteButton} /> </a>
  )
}

export default Browser
