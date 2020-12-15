function UsersComponent(api) {
  return {
    data: function () {
      return {
        users: [],
        debug: {},
        search: {
          first_name_prefix: null,
          last_name_prefix: null
        }
      }
    },

    methods: {
      refresh: function () {
        this.debug = {'loadUsers': '/users'}
        let params = this.search;
        api.get('/users/', {params: params})
          .then(response => {
            this.users = response.data;
            this.debug = {'loadUsers': 'success'}
          })
          .catch(error => {
            if (error.response) {
              this.debug = error.response.data;
            } else {
              this.debug = {'loadProfile': 'error', 'detail': 'See console errors and try again!'}
            }
          })
      }
    },
    mounted() {
      this.refresh();
    },

    template: '#users'
  }
}

function UsersApp(api) {
  let app = Vue.createApp({});
  app.component('users', UsersComponent(api))
  app.mount('#users-app');
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

  UsersApp(api);
})();