/**
 * In this file, we create a React component
 * which incorporates components provided by Material-UI.
 */
import React, { Component } from 'react';
import { deepOrange400, deepOrange500 } from 'material-ui/styles/colors';

import { List, ListItem } from 'material-ui/List';
import RaisedButton from 'material-ui/RaisedButton';
import Subheader from 'material-ui/Subheader';
import Divider from 'material-ui/Divider';

import IconButton from 'material-ui/IconButton'
import ActionDelete from 'material-ui/svg-icons/action/delete'
import LockClosed from 'material-ui/svg-icons/action/lock';
import LockOpen from 'material-ui/svg-icons/action/lock-open';
import LinkIcon from 'material-ui/svg-icons/editor/insert-link';

function Browser(props) {
  const { folder, files, folders, token, changeFolder, onDelete, tags, onPublicSet } = props

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
        tags={tags[file]}
        onPublicSet={onPublicSet}
      />)}
    </List>
  </div>)
}

function FolderItem(props) {
  const { name, changeFolder } = props

  return (
    <ListItem
      primaryText={name}
      onTouchTap={() => changeFolder(`/${name}`)} />
  )
}

function FileItem(props) {
  const { name, onDelete, tags, onPublicSet } = props

  const deleteFile = e => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm(`Delete ${name}?`)) fetch(`/${name}?token=${props.token}`, { method: 'DELETE' }).then(onDelete)
  }

  const deleteButton = (
    <IconButton
      title="Radera"
      style={{ boxShadow: 'none' }}
      hoveredStyle={{ boxShadow: 'none' }}
      onClick={deleteFile}>
      <ActionDelete hoverColor={deepOrange500} />
    </IconButton>
  )
  const constructShortUrl = (short) => window.location.origin + "/" + short;
  const copyToClipboard = (short) => {
    const value = constructShortUrl(short);
    // navigator clipboard api needs a secure context (https)
    if (navigator.clipboard && window.isSecureContext) {
      // navigator clipboard api method'
      return navigator.clipboard.writeText(value);
    } else {
      // text area method
      const textArea = document.createElement("textarea");
      textArea.value = value;
      // make the textarea out of viewport
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      textArea.style.top = "-999999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      return new Promise((res, rej) => {
        // here the magic happens
        document.execCommand('copy') ? res() : rej();
        textArea.remove();
      });
    }
  }


  const copyButton = (
    <IconButton
      title="Kopiera länk"
      style={{ boxShadow: 'none' }}
      hoveredStyle={{ boxShadow: 'none' }}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        copyToClipboard(name)
      }}>
      <LinkIcon hoverColor={deepOrange500} />
    </IconButton>
  )

  
  const isPublic = tags
                  .filter(t => t["Key"] === "public")[0]["Value"]
                  .toLowerCase() === "true"
  
  const AccessibleIcon = (
    <IconButton
      style={{ boxShadow: 'none' }}
      hoveredStyle={{ boxShadow: 'none' }}
      title={isPublic ? "Öppen för alla på internet" : "Ej öppen för alla på internet, åtkomst via yoggi krävs."}
      onClick={e => {
        e.preventDefault()
        e.stopPropagation()
        onPublicSet(name, isPublic)
      }}
    >
      {isPublic ?
        <LockOpen hoverColor={deepOrange500} />
        :
        <LockClosed hoverColor={deepOrange500} />
      }
    </IconButton>
  )

  return (
    <a href={isPublic ? `https://${process.env.REACT_APP_BUCKET_NAME}.s3.amazonaws.com/${name}` : `/${name}`} target="_blank" rel="noopener noreferrer">
      <ListItem
        primaryText={name}
        rightIconButton={
          <div>
            {copyButton}
            {AccessibleIcon}
            {deleteButton}
          </div>}
      />
    </a>
  )
}

export default Browser
