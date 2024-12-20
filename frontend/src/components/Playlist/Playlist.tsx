import React, { useState, useEffect } from 'react';
import { MDBIcon, MDBBtn, MDBTable, MDBTableHead, MDBTableBody, MDBInput } from 'mdb-react-ui-kit';

import { useSocket } from "../../contexts/SocketContext";
import { AgentMessage, ChatMessage, Annotation, Song, Response } from "../../types";

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

    socket?.on("playlist", (data: Song[]) => { // Errors here
      setPlaylist(data);
    });
  });

  const handleAgentRemoveSong = (annotations: Annotation[]) => {
    const song: Song = {}
    annotations.map((annotation) => 
      {
        song.title = annotation.value.title
        song.artist = annotation.value.artist
        song.album = annotation.value.album
      }
    )

    if (song.title && song.artist) {
      setPlaylist((prevPlaylist) =>
        prevPlaylist.filter(
          (item) =>
            item.title?.toLowerCase() !== song.title?.toLowerCase() ||
            item.artist?.toLowerCase() !== song.artist?.toLowerCase()
        )
      );
    }
  }

  const handelMessageForPlaylist = (message: ChatMessage) => {
    const intent = message.intent
    const annotations: Annotation[] = message.annotations
    console.log(annotations)

    if (intent === "add") {
      
    }
    else if (intent === "remove") {
      handleAgentRemoveSong(annotations)
    }
    else if (intent === "clear") {
      setPlaylist([])
    }
  };

  const handleAddSong = () => {
    if (newSong.title && newSong.artist && newSong.album) {
      const song: Song = {
        title: newSong.title,
        artist: newSong.artist,
        album: newSong.album
      };

      socket?.emit("add", {add: song}); 
      socket?.on("add:response", (response: Response) => {
        if (response.status === "OK") {
          setPlaylist([...playlist, song]);
          setNewSong({ title: '', artist: '', album: '' }); // Clear input fields after adding
        }
        setIsAddingRow(false);
      })
    }
  };

  const handleRemoveSong = (index: number) => {
    socket?.emit("remove", {remove: playlist[index]})

    const updatedPlaylist = playlist.filter((_, i) => i !== index);
    setPlaylist(updatedPlaylist);
  };

  const handleNewRowClick = () => {
    setIsAddingRow(true); // Show input fields for a new row
  };  

  const handleClearPlaylist = () => {
    socket?.emit("clear", {})
    setPlaylist([]);
  };

  return (
    <div className='mt-5' style={{ width: '100%' }}>
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

                <MDBBtn color='info' onClick={() => handleClearPlaylist()} style={{ width: '100px', marginLeft: '10px', marginRight: '10px'}}>
                  Clear
                </MDBBtn>
              </td>
            </tr>
          )}
        </MDBTableBody>
      </MDBTable>
    </div>
  );
}
