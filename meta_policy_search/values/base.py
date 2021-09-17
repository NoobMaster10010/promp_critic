from meta_policy_search.utils.utils import remove_scope_from_name
from meta_policy_search.utils import Serializable
import tensorflow as tf
from collections import OrderedDict


class Value_net(Serializable):
    """
    Args:
        obs_dim (int)                   : dimensionality of the observation space 
        action_dim (int)                : dimensionality of the action space 

        name (str)                      : Name used for scoping variables in value_net
        hidden_sizes (tuple)            : size of hidden layers of network
        hidden_nonlinearity (Operation) : nonlinearity used between hidden layers of network
        output_nonlinearity (Operation) : nonlinearity used after the final layer of network
    """
    def __init__(self,
                 ob_dim,
                 task_id_dim,
                 name,
                 hidden_sizes         =(32, 32),
                 hidden_nonlinearity  =tf.nn.relu,
                 output_nonlinearity  =None,
                 **kwargs
                 ):
        Serializable.quick_init(self, locals())

        self.ob_dim              = ob_dim
        self.task_id_dim         = task_id_dim
        self.name                = name


        self.hidden_sizes        = hidden_sizes
        self.hidden_nonlinearity = hidden_nonlinearity
        self.output_nonlinearity = output_nonlinearity

        self.value_net_params         = None

        self._assign_ops              = None
        self._assign_phs              = None



    def build_graph(self):
        """
        Builds computational graph for value_net
        """
        raise NotImplementedError

    def get_state_value(self, observation, task_id):
        """
        Runs a single observation through the specified value_net

        Args:
            observation (array) : single observation

        Returns:
            (array) : array of arrays of actions for each env
        """
        raise NotImplementedError

    def get_state_values(self, observations, task_ids):
        """
        Runs each set of observations through each task specific value_net

        Args:
            observations (array) : array of arrays of observations generated by each task and env

        Returns:
            (tuple) : array of arrays of actions for each env (meta_batch_size) x (batch_size) x (action_dim)
                      and array of arrays of agent_info dicts 
        """
        raise NotImplementedError



    def get_next_state_value(self, next_observation, next_task_id):
        """
        Runs a single observation through the specified value_net

        Args:
            observation (array) : single observation

        Returns:
            (array) : array of arrays of actions for each env
        """
        raise NotImplementedError

    def get_next_state_values(self, next_observations, next_task_ids):
        """
        Runs each set of observations through each task specific value_net

        Args:
            observations (array) : array of arrays of observations generated by each task and env

        Returns:
            (tuple) : array of arrays of actions for each env (meta_batch_size) x (batch_size) x (action_dim)
                      and array of arrays of agent_info dicts 
        """
        raise NotImplementedError


    def log_diagnostics(self, paths):
        """
        Log extra information per iteration based on the collected paths
        """
        pass


    """ --- methods for serialization --- """

    def get_params(self):
        """
        Get the tf.Variables representing the trainable weights of the network (symbolic)

        Returns:
            (dict) : a dict of all trainable Variables
        """
        return self.value_net_params

    def get_param_values(self):
        """
        Gets a list of all the current weights in the network (in original code it is flattened, why?)

        Returns:
            (list) : list of values for parameters
        """
        param_values = tf.get_default_session().run(self.value_net_params)
        return param_values

    def set_params(self, value_net_params):
        """
        Sets the parameters for the graph

        Args:
            value_net_params (dict): of variable names and corresponding parameter values
        """
        assert all([k1 == k2 for k1, k2 in zip(self.get_params().keys(), value_net_params.keys())]), \
            "parameter keys must match with variable"

        if self._assign_ops is None:
            assign_ops, assign_phs = [], []
            for var in self.get_params().values():
                assign_placeholder = tf.placeholder(dtype=var.dtype)
                assign_op = tf.assign(var, assign_placeholder)
                assign_ops.append(assign_op)
                assign_phs.append(assign_placeholder)
            self._assign_ops = assign_ops
            self._assign_phs = assign_phs
        feed_dict = dict(zip(self._assign_phs, value_net_params.values()))
        tf.get_default_session().run(self._assign_ops, feed_dict=feed_dict)

    def __getstate__(self):
        state = {
            'init_args':      Serializable.__getstate__(self),
            'network_params': self.get_param_values()
        }
        return state

    def __setstate__(self, state):
        Serializable.__setstate__(self, state['init_args'])
        tf.get_default_session().run(tf.global_variables_initializer())
        self.set_params(state['network_params'])