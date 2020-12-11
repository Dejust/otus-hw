function getUserID() {
  const urlParams = new URLSearchParams(window.location.search);
  const userId = urlParams.get('userId');
  if (userId) {
    return parseInt(userId);
  }
  return getLoggedUserId();
}

function UserDetailsComponent(api) {
  return {
    data() {
      return {
        updatable: false,
        debug: {},
        profile: {}
      }
    },

    methods: {
      refresh: function () {
        const url = '/users/' + getUserID();
        this.debug = {'loadProfile': url}

        api.get(url)
          .then(response => {
            this.profile = response.data.profile;
            this.debug = {'loadProfile': 'success'}
          })
          .catch(error => {
            if (error.response) {
              this.debug = error.response.data;
            } else {
              this.debug = {'loadProfile': 'error', 'detail': 'See console errors and try again!'}
            }
          })
      },

      update: function () {
        this.debug = {'updateProfile': '/users/me'}

        api.put('/users/me', this.profile)
          .then(response => {
            this.profile = response.data;
            this.debug = {'updateProfile': 'success'}
          })
          .catch(error => {
            if (error.response) {
              this.debug = error.response.data;
            } else {
              this.debug = {'updateProfile': 'error', 'detail': 'See console errors and try again!'}
            }
          })
      },
    },

    mounted() {
      this.refresh();
    },

    template: '#user-details'
  }
}

function FriendsComponent(api) {
  return {
    data() {
      return {
        debug: {},
        friends: []
      }
    },

    methods: {
      canSendRequest() {
        return getLoggedUserId() !== getUserID();
      },

      sendFriendRequest: function () {
        const urlParams = new URLSearchParams(window.location.search);
        const targetUserId = urlParams.get('userId');
        if (!targetUserId) {
          return;
        }

        api.post('/users/' + getLoggedUserId() + '/friends', {'target_user_id': targetUserId})
          .then(_ => {
            this.refresh();
          }).catch(error => {
            if (error.response && error.response.status === 409) {
              alert('This user is you friend! Check your profile.')
            }
        })
      },

      del(friendId) {
        const url = '/users/' + getUserID() + '/friends/' + friendId;
        api.delete(url)
          .then(_ => {
            this.refresh()
          })
      },

      refresh() {
        const url = '/users/' + getUserID() + '/friends';
        this.debug = {'loadFriends': url}
        api.get(url)
          .then(response => {
            this.friends = response.data;
            this.debug = {'loadFriends': 'success'}
          })
          .catch(error => {
            if (error.response) {
              this.debug = error.response.data;
            } else {
              this.debug = {'loadFriends': 'error', 'detail': 'See console errors and try again!'}
            }
          })
      }
    },

    mounted() {
      this.refresh();
    },

    template: '#friends'
  }
}

function ProfileApp(api) {
  let app = Vue.createApp({});
  app.component('user-details', UserDetailsComponent(api));
  app.component('friends', FriendsComponent(api));
  app.mount('#profile-app');
}


(function () {
  if (!userLogged()) {
    window.location.replace('/')
  }

  const api = axios.create({
    baseURL: '/api/',
    timeout: 5000,
    headers: {'Authorization': 'Bearer ' + getAuthToken()}
  });

  ProfileApp(api);
})();