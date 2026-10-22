#include<iostream>
#include<malloc.h>
#include<time.h>
#include<stdlib.h>
#include<math.h>

#define LEN sizeof(struct ES)
//coded and modified by Dr. Qiang Ye
using namespace std;
float tc; // current time instant
int SN; // sending sequence number
int RN; // receiving sequence number (next expected frame sequence number)
int Num_received_frames; // number of successfully received frames
int Next_Expect_Frame ; // same as RN
int Next_Expect_ACK ; // SN +1 mod 2
int Type_1 = 0; // ACK event
int Type_2 = 1; // Timeout event
int Flag_forward; // Forward channel error indicator
int Flag_ACK; // Reverse channel error indicator
int Flag_timeout = -1;
int Sequence_timeout = -1;
float Timeout = 0.0;
float H = 54 * 8; // header = 54 bytes
float payload_length = 1500 * 8; // packet payload = 1500 bytes
float frame_length = H + payload_length; // header + payload
float tau = 250 * 0.001; // one-way propagation delay 250ms, adjustable
float delta = 5 * tau; // ACK timeout 5 times propagation delay, adjustable
float C = 5 * 1000000; // channel rate 5Mb/s
float BER = 0.00001; // bit error rate
int Limit = 10000; // Maximum No. of received packets to end simulation
float simu_start_time; // simulation start time
float simu_end_time = 0.0; // simulation end time
int n = 0;
int L1 = 1500 * 8 + 54 * 8; // bit length of entire packet including header
int L2 = 54 * 8; // bit length of ACK
struct ES{
    int type;
    float time;
    int error_flag;
    int sequence_no;
    struct ES * next;
};

struct ES *head = NULL;
struct ES *tail = NULL;

void insert_event(int Type, float Time, int F, int S){
    struct ES * p1, * p2, * p3;
    p1 = (struct ES *) malloc(LEN);
    p1 -> type = Type;
    p1 -> time = Time;
    p1 -> error_flag = F;
    p1 -> sequence_no = S;
    p1 -> next = NULL;
    p2 = head; // search the entire linked list from head node
    if (p2 == NULL){ // no head node exists, which means p1 is the first node to be inserted
        //
    }
    else
    {
        while ((p1 -> time > p2 -> time) && (p2 -> next != NULL)) /* When time of inserted node is greater than that of the searched node*/
        {
             /* p3 points to the former one*/
             /* p2 moves to the next one*/
        }
        if (p1 -> time <= p2 -> time) /* If time of inserted node is smaller than that of searched node*/
        {
            if (p2 == head)
            {
        	     /* Insert before the first one*/
            }
            else
            {
                /* Insert after former one*/
            }
             // insert before currently searched node
        }
        else // search to the last node
        {
            //p1 inserted as the last node
        }
    }
    n = n + 1;
}
void delete_event(){
    struct ES * p1 = head;
    head = p1 -> next;
    n = n - 1;
    delete(p1);
}
void Initialization(){
    tc = 0.0;
    Num_received_frames = 0;
    simu_start_time = tc;
    SN = 0;
    Next_Expect_ACK = (SN + 1)%2;
    Next_Expect_Frame = 0;
    RN = Next_Expect_Frame;
    tc = tc + frame_length/C;
    Timeout = tc + delta;
    insert_event(Type_2, Timeout, Flag_timeout, Sequence_timeout);
}
void send(int L_1, int L_2){ //send packet from sender to receiver
    float x,y;
    int i;
    int count_1 = 0; // indicate the status of forward channel
    for (i = 0; i < L_1; i++){
         // generate a random decimal between 0 and 1
        if (x < BER){
            //update counter 1
        }
    }
    if (count_1 >= 5){ // if it has more than 5 erroneous bits
         // data frame is lost, update forward channel flag
    }
    else if ((count_1 < 5) && (count_1 > 0)){
        // data frame is in error, update forward channel flag
        tc = tc + tau; // update current time instant by adding the propagation delay
    }
    else{
        // data frame is error free, update forward channel flag
        tc = tc + tau; // update current time instant
    }
    int count_2 = 0;
    for (i = 0; i < L_2; i++){
        //randomly generate a decimal number between 0 and 1
        if (y < BER){
            // if bit is in error update reverse channel status indicator
        }
    }
    if (count_2 >= 5){
         // ACK lost, update reverse channel status indicator
    }
    else if ((count_2 < 5) && (count_2 > 0)){
        // ACK error, update reverse channel status indicator
    }
    else{
        // ACK error free, update reverse channel status indicator
    }
    if (Flag_forward == 0){ // no error on the forward channel
        // update Next_Expected_Frame
        // update RN
        tc = tc + H/C; // Assume ACK length is same as header length H, update current time instant
        tc = tc + tau;
        insert_event(Type_1, tc, Flag_ACK, RN); // insert type 1 event into the linked list
    }
    else if (Flag_forward == 1){ //error occurs on the forwarded channel
         // RN needs to be updated?
        // update current time
        if (Flag_ACK != 2){
            //update current time
            insert_event(Type_1, tc, Flag_ACK, RN); // insert type 1 event into the linked list
        }
    }
}
int main(){
    struct ES *temp;
    float Throughput = 0.0;
    float Total_simu_time = 0.0;
    Initialization();
    send(L1, L2);
    while (head != NULL){
        temp = head;
        if ((temp->type == Type_1) && (temp->sequence_no == Next_Expect_ACK))
        {
            // update SN
             // update Next_Expected_ACK
            // update Num_received_frames
            if (Num_received_frames >= Limit){
                simu_end_time = temp->time;
                break;
            }
             // tc set to the end of transmission time of the next packet
             // set a new timeout for the next packet
            // delete type 1 event
            // also delete the type 2 event associated with the type 1 event
            insert_event(Type_2, Timeout, Flag_timeout, Sequence_timeout); // insert timeout event for the next packet
            send(L1, L2); // send out the next packet
        }
        else if ((temp->type == Type_1) && (temp->sequence_no != Next_Expect_ACK)){
            // delete type 1 event
        }
        else if (temp->type == Type_2){
            //tc set to the end of retransmission time of the packet
            // set a new timeout for the retransmitted packet
            // delete type 2 event
            insert_event(Type_2, Timeout, Flag_timeout, Sequence_timeout);
            send(L1, L2);
        }
    }
    Total_simu_time = simu_end_time - simu_start_time;
    Throughput = ((float)Num_received_frames * payload_length)*0.001/Total_simu_time; //kbps
    cout << "Throughput = " << Throughput << "kbps" << endl;
    cout << "Successfully Transmitted Frames = " << Num_received_frames << " frames" << endl;
    cout << "Total Simulation Time = " << Total_simu_time << " s" << endl;
    return 0;
}

