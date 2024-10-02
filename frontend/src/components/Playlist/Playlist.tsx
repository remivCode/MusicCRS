import React, { useState } from 'react';
import { MDBIcon, MDBBtn, MDBTable, MDBTableHead, MDBTableBody, MDBInput } from 'mdb-react-ui-kit';

export default function Playlist() {
  const [playlist, setPlaylist] = useState([
    { title: 'Die With A Smile', artist: 'Lady Gaga, Bruno Mars', album: 'Die With A Smile' },
  ]);
  const [newSong, setNewSong] = useState({ title: '', artist: '', album: '' });
  const [isAddingRow, setIsAddingRow] = useState(false);

  const handleAddSong = () => {
    if (newSong.title && newSong.artist && newSong.album) {
      setPlaylist([...playlist, newSong]);
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
            <MDBBtn color='link' rounded size='sm' onClick={() => handleNewRowClick()}>
              <MDBIcon fas icon="plus" size='lg' />
            </MDBBtn>
          )}
        </MDBTableBody>
      </MDBTable>
    </div>
  );
}
