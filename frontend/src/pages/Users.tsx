import React, { useEffect, useState } from 'react';
import api from '../api/api';

const UsersPage = () => {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    api.get('/admin/users')
      .then(res => setUsers(res.data.users))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h2>All Users</h2>
      <ul>
        {users.map((user: any) => (
          <li key={user._id}>{user.username}</li>
        ))}
      </ul>
    </div>
  );
};

export default UsersPage; 