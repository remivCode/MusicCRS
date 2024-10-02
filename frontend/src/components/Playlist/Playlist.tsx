import React, { useState, useEffect } from 'react';
import { MDBIcon, MDBBtn, MDBTable, MDBTableHead, MDBTableBody, MDBInput } from 'mdb-react-ui-kit';

import { useSocket } from "../../contexts/SocketContext";
import { AgentMessage, ChatMessage, Annotation, Song } from "../../types";

export default function Playlist() {
  const [playlist, setPlaylist] = useState<Song[]>([]);
  const [newSong, setNewSong] = useState({ title: '', artist: '', album: '' });
  const [isAddingRow, setIsAddingRow] = useState(false);
  const { socket } = useSocket();

  useEffect(() => {
    socket?.on("message", (response: AgentMessage) => {
      if (response.info) {
        console.log(response.info);
      }
      if (response.message) {
        handelMessageForPlaylist(response.message);
      }
    });
    });

    const handleAgentAddSong = (annotations: Annotation[]) => {
      const song: Song = {}
      annotations.map((annotation) => 
        {
          if (annotation.slot === "title") {
            song.title = annotation.value
          } else if (annotation.slot === "artist") {
            song.artist = annotation.value
          } else if (annotation.slot === "album") {
            song.album = annotation.value
          }
        }
      )
  
      if (song.title && song.artist) {
        setPlaylist([...playlist, song]);
      }
    }

  const handelMessageForPlaylist = (message: ChatMessage) => {
    const intent = message.intent
    const annotations: Annotation[] = message.annotations

    if (intent === "add") {
      handleAgentAddSong(annotations)
    }
  };

  const handleAddSong = () => {
    if (newSong.title && newSong.artist && newSong.album) {
      const song: Song = {
        title: newSong.title,
        artist: newSong.artist,
        album: newSong.album
      };
      setPlaylist([...playlist, song]);
      setNewSong({ title: '', artist: '', album: '' }); // Clear input fields after adding
      setIsAddingRow(false);
    }
  };

  const handleRemoveSong = (index: number) => {
    const updatedPlaylist = playlist.filter((_, i) => i !== index);
    setPlaylist(updatedPlaylist);
  };

  const handleNewRowClick = () => {
    setIsAddingRow(true); // Show input fields for a new row
  };  

  return (
    <div className='mt-5'>
      {/* Playlist display */}
      <MDBTable align='middle'>
        <MDBTableHead>
          <tr>
            <th scope='col'>Title</th>
            <th scope='col'>Artist</th>
            <th scope='col'>Album</th>
            <th scope='col'>Delete</th>
          </tr>
        </MDBTableHead>
        <MDBTableBody>
          {playlist.map((song, index) => (
            <>
              <tr key={index}>
                <td>
                  <div className='d-flex align-items-center'>
                    <div className='ms-3'>
                      <p className='fw-bold mb-1'>{song.title}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <p className='fw-normal mb-1'>{song.artist}</p>
                </td>
                <td>{song.album}</td>
                <td>
                  <MDBBtn color='link' rounded size='sm' onClick={() => handleRemoveSong(index)}>
                    <MDBIcon fas icon="trash" size='lg' />
                  </MDBBtn>
                </td>
              </tr>
            </>
          ))}

          {/* Conditionally render input row */}
          {isAddingRow && (
            <tr>
              <td>
                <MDBInput
                  label="Title"
                  value={newSong.title}
                  onChange={(e) => setNewSong({ ...newSong, title: e.target.value })}
                />
              </td>
              <td>
                <MDBInput
                  label="Artist"
                  value={newSong.artist}
                  onChange={(e) => setNewSong({ ...newSong, artist: e.target.value })}
                />
              </td>
              <td>
                <MDBInput
                  label="Album"
                  value={newSong.album}
                  onChange={(e) => setNewSong({ ...newSong, album: e.target.value })}
                />
              </td>
              <td>
              <MDBBtn color='link' rounded size='sm' onClick={() => handleAddSong()}>
                    <MDBIcon fas icon="check" size='lg' />
                  </MDBBtn>
              </td>
            </tr>
          )}

          {!isAddingRow && (
            <tr>
              <td>
                <MDBBtn color='link' rounded size='sm' onClick={() => handleNewRowClick()}>
                  <MDBIcon fas icon="plus" size='lg' />
                </MDBBtn>
              </td>
            </tr>
          )}
        </MDBTableBody>
      </MDBTable>
    </div>
  );
}
