import React from 'react';
import { MDBIcon, MDBBadge, MDBBtn, MDBTable, MDBTableHead, MDBTableBody } from 'mdb-react-ui-kit';

export default function Playlist() {
  return (
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
        <tr>
          <td>
            <div className='d-flex align-items-center'>
              <div className='ms-3'>
                <p className='fw-bold mb-1'>Die With A Smile</p>
              </div>
            </div>
          </td>
          <td>
            <p className='fw-normal mb-1'>Lady Gaga, Bruno Mars</p>
          </td>
          <td>Die With A Smile</td>
          <td>
            <MDBBtn color='link' rounded size='sm'>
              <MDBIcon fas icon="trash" size='lg'/>
            </MDBBtn>
          </td>
        </tr>
      </MDBTableBody>
    </MDBTable>
  );
}