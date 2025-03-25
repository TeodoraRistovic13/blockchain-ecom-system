// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

contract OrderContract {
    address payable public buyer;
    uint256 public orderAmount;
    bool public paid;
    bool public delivered;
    address payable public courier;
    address payable public owner; // Added store owner address

    enum State { CREATED, PAID, DELIVERED, CLOSED }
    State public state;

    mapping(State => string) stateNames;


     modifier onlyInState(State _state) {
        require(state == _state, stateNames[state]);
        _;
     }

    modifier onlyBuyer() {
        require(msg.sender == buyer, "Only the buyer can call this function");
        _;
    }

    constructor(address payable _buyer, uint256 _orderAmount) {
        buyer = _buyer;
        orderAmount = _orderAmount;
        courier = payable(address(0));  // Initialize courier as empty
        owner = payable(msg.sender); // Assign the contract deployer as the store owner
        state = State.CREATED;
        stateNames[State.CREATED] = "CREATED";
        stateNames[State.PAID] = "PAID";
        stateNames[State.DELIVERED] = "DELIVERED";
        stateNames[State.CLOSED] = "CLOSED";
    }

    // Function for the buyer to make payment for the order
    function makePayment() public payable onlyBuyer onlyInState(State.CREATED) {

        require(msg.value == orderAmount, "Payment amount does not match the order amount");
        state = State.PAID;
    }

    // Function for couriers to accept the order for delivery
    function acceptOrder(address payable _courier) public onlyInState(State.PAID) {

        require(courier == address(0), "Order already assigned to a courier");
        courier = _courier;
        state = State.DELIVERED;
    }

    // Function for the buyer to confirm delivery
    function confirmDelivery() public onlyBuyer onlyInState (State.DELIVERED) {

        uint256 ownerShare = (orderAmount * 80) / 100;
        owner.transfer(ownerShare);
        courier.transfer(orderAmount - ownerShare);

        state = State.CLOSED;
    }
}
