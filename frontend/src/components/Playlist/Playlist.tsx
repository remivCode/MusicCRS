import React, { useState } from 'react';
import { MDBIcon, MDBBtn, MDBTable, MDBTableHead, MDBTableBody, MDBInput } from 'mdb-react-ui-kit';

export default function Playlist() {
  const [showHelp, setShowHelp] = useState(false);
  const [playlist, setPlaylist] = useState([
    { title: 'Die With A Smile', artist: 'Lady Gaga, Bruno Mars', album: 'Die With A Smile' },
  ]);
  const [newSong, setNewSong] = useState({ title: '', artist: '', album: '' });

  const handleToggleHelp = () => {
    setShowHelp(!showHelp);
  };

  const handleAddSong = () => {
    if (newSong.title && newSong.artist && newSong.album) {
      setPlaylist([...playlist, newSong]);
      setNewSong({ title: '', artist: '', album: '' }); // Clear input fields after adding
    }
  };

  const handleRemoveSong = (index: number) => {
    const updatedPlaylist = playlist.filter((_, i) => i !== index);
    setPlaylist(updatedPlaylist);
  };
  

  return (
    <>
      <MDBBtn color='info' onClick={handleToggleHelp}>
        {showHelp ? 'Hide Help' : 'Show Help'}
      </MDBBtn>

      {showHelp && (
        <div className='mt-3'>
          <h4>Available Commands:</h4>
          <ul>
            <li><strong>add &lt;artist&gt; - &lt;title&gt;</strong>: Add a song to the playlist</li>
            <li><strong>remove &lt;artist&gt; - &lt;title&gt;</strong>: Remove a song from the playlist</li>
            <li><strong>clear</strong>: Clear the playlist</li>
            <li><strong>show</strong>: Show the playlist</li>
            <li><strong>EXIT</strong>: End the conversation</li>
          </ul>
        </div>
      )}

      {/* Form to add a new song */}
      <div className="mt-4 mb-4">
        <h5>Add a new song:</h5>
        <MDBInput
          label="Title"
          value={newSong.title}
          onChange={(e) => setNewSong({ ...newSong, title: e.target.value })}
          className="mb-2"
        />
        <MDBInput
          label="Artist"
          value={newSong.artist}
          onChange={(e) => setNewSong({ ...newSong, artist: e.target.value })}
          className="mb-2"
        />
        <MDBInput
          label="Album"
          value={newSong.album}
          onChange={(e) => setNewSong({ ...newSong, album: e.target.value })}
          className="mb-2"
        />
        <MDBBtn color='success' onClick={handleAddSong}>
          Add Song
        </MDBBtn>
      </div>

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
          ))}
        </MDBTableBody>
      </MDBTable>
    </>
  );
}
